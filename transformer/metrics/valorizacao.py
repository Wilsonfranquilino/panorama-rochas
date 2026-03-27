import duckdb
import logging

logger = logging.getLogger(__name__)

def calcular_valorizacao(con: duckdb.DuckDBPyConnection):
    logger.info("Valorização: calculando monitor de upgrading sobre dados curados")

    # 1. Base de Categorização (Bruto vs Beneficiado)
    # A gold_preco_produto já vem com os totais de volume e FOB agregados
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
                WHEN produto ILIKE '%bruto%' OR produto ILIKE '%raw%' OR produto ILIKE '%bloco%'
                    THEN 'Bruto'
                ELSE 'Beneficiado'
            END AS categoria
        FROM gold_preco_produto
    )
    SELECT
        ano_mes,
        produto,
        categoria,
        volume_m2,
        fob_usd,
        preco_m2_usd,
        -- Variação YoY (Comparação com o mesmo mês do ano anterior)
        preco_m2_usd - LAG(preco_m2_usd, 12) OVER (
            PARTITION BY produto ORDER BY ano_mes
        ) AS variacao_yoy_usd,
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

    # 2. Upgrading Ratio (Eficiência Industrial)
    # Mede quantas vezes o beneficiado vale mais que o bruto no período
    con.execute("""
    CREATE OR REPLACE TABLE metric_upgrading_ratio AS
    SELECT
        ano_mes,
        -- Usamos AVG para ter o preço médio da categoria no mês, caso haja múltiplos produtos
        AVG(CASE WHEN categoria = 'Beneficiado' THEN preco_m2_usd END) AS preco_beneficiado,
        AVG(CASE WHEN categoria = 'Bruto'        THEN preco_m2_usd END) AS preco_bruto,
        ROUND(
            AVG(CASE WHEN categoria = 'Beneficiado' THEN preco_m2_usd END) /
            NULLIF(AVG(CASE WHEN categoria = 'Bruto' THEN preco_m2_usd END), 0)
        , 2) AS ratio_upgrading
    FROM metric_valorizacao
    GROUP BY ano_mes
    ORDER BY ano_mes
    """)

    n = con.execute("SELECT COUNT(*) FROM metric_upgrading_ratio").fetchone()[0]
    logger.info(f"Valorização: monitor calculado para {n} períodos")