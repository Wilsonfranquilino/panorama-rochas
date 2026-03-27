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

    # --- PASSO 2: Upgrading Ratio (Eficiência Industrial Consolidada) ---
    # CORREÇÃO DEFINITIVA: Calculamos a média por categoria por mês para ter o Ratio Real
    con.execute("""
    CREATE OR REPLACE TABLE metric_upgrading_ratio AS
    WITH medias AS (
        SELECT
            ano_mes,
            AVG(CASE WHEN categoria = 'Beneficiado' THEN preco_m2_usd END) AS preco_beneficiado,
            AVG(CASE WHEN categoria = 'Bruto'        THEN preco_m2_usd END) AS preco_bruto
        FROM metric_valorizacao
        GROUP BY ano_mes
    )
    SELECT
        ano_mes,
        preco_beneficiado,
        preco_bruto,
        ROUND(preco_beneficiado / NULLIF(preco_bruto, 0), 2) AS ratio_upgrading
    FROM medias
    ORDER BY ano_mes
    """)

    # Verificação de saída para o log
    n_ratio = con.execute("SELECT COUNT(*) FROM metric_upgrading_ratio").fetchone()[0]
    n_val = con.execute("SELECT COUNT(*) FROM metric_valorizacao").fetchone()[0]
    
    logger.info(f"Valorização: Monitor finalizado. {n_val} registros de valorização e {n_ratio} registros de ratio gerados.")