import duckdb
import logging

logger = logging.getLogger(__name__)

def calcular_valorizacao(con: duckdb.DuckDBPyConnection):
    logger.info("Valorização: Iniciando cálculo individualizado por produto e categoria.")

    # --- PASSO 1: Base de Categorização e Variação YoY ---
    # CORREÇÃO: Usamos PARTITION BY produto para que a variação de um material não suje a do outro.
    con.execute("""
    CREATE OR REPLACE TABLE metric_valorizacao AS
    WITH base AS (
        SELECT
            ano_mes,
            produto,
            volume_m2,
            fob_usd,
            preco_m2_usd,
            CASE
                WHEN (produto ILIKE '%bruto%' OR produto ILIKE '%raw%' OR produto ILIKE '%bloco%')
                    THEN 'Bruto'
                ELSE 'Beneficiado'
            END AS categoria
        FROM gold_preco_produto
    )
    SELECT
        *,
        -- Cálculo de variação USD absoluto
        preco_m2_usd - LAG(preco_m2_usd, 12) OVER (
            PARTITION BY produto ORDER BY ano_mes
        ) AS variacao_yoy_usd,
        
        -- Cálculo de variação Percentual (%) individual por produto
        ROUND(
            (preco_m2_usd - LAG(preco_m2_usd, 12) OVER (
                PARTITION BY produto ORDER BY ano_mes
            )) * 100.0 / NULLIF(LAG(preco_m2_usd, 12) OVER (
                PARTITION BY produto ORDER BY ano_mes
            ), 0)
        , 2) AS variacao_yoy_pct
    FROM base
    ORDER BY ano_mes, produto
    """)

    # --- PASSO 2: Upgrading Ratio (Eficiência Industrial por Material) ---
    # CORREÇÃO CRÍTICA: Adicionado 'produto' no GROUP BY. 
    # Isso impede a média global que estava deixando todos os materiais iguais.
    con.execute("""
    CREATE OR REPLACE TABLE metric_upgrading_ratio AS
    SELECT
        ano_mes,
        produto, 
        -- Média do preço beneficiado para este produto específico no mês
        AVG(CASE WHEN categoria = 'Beneficiado' THEN preco_m2_usd END) AS preco_beneficiado,
        
        -- Média do preço bruto para este produto específico no mês
        AVG(CASE WHEN categoria = 'Bruto'        THEN preco_m2_usd END) AS preco_bruto,
        
        -- Ratio real: Quantas vezes o beneficiado é mais caro que o bruto para ESTE material
        ROUND(
            AVG(CASE WHEN categoria = 'Beneficiado' THEN preco_m2_usd END) /
            NULLIF(AVG(CASE WHEN categoria = 'Bruto' THEN preco_m2_usd END), 0)
        , 2) AS ratio_upgrading
    FROM metric_valorizacao
    GROUP BY ano_mes, produto
    ORDER BY ano_mes, produto
    """)

    # Verificação de saída para o log
    n_ratio = con.execute("SELECT COUNT(*) FROM metric_upgrading_ratio").fetchone()[0]
    n_val = con.execute("SELECT COUNT(*) FROM metric_valorizacao").fetchone()[0]
    
    logger.info(f"Valorização: Monitor finalizado. {n_val} registros de valorização e {n_ratio} registros de ratio gerados.")