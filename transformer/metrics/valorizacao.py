"""
Métrica 3: Monitor de Valorização do Produto
Acompanha evolução do preço médio por m² — bruto vs beneficiado
"""
import duckdb
import logging; logger = logging.getLogger(__name__)

def calcular_valorizacao(con: duckdb.DuckDBPyConnection):
    logger.info("Valorização: calculando monitor de upgrading")

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
                WHEN produto ILIKE '%bruto%' OR produto ILIKE '%raw%'
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
        -- variação YoY
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

    # Razão beneficiado/bruto por período
    con.execute("""
    CREATE OR REPLACE TABLE metric_upgrading_ratio AS
    SELECT
        ano_mes,
        MAX(CASE WHEN categoria = 'Beneficiado' THEN preco_m2_usd END) AS preco_beneficiado,
        MAX(CASE WHEN categoria = 'Bruto'        THEN preco_m2_usd END) AS preco_bruto,
        ROUND(
            MAX(CASE WHEN categoria = 'Beneficiado' THEN preco_m2_usd END) /
            NULLIF(MAX(CASE WHEN categoria = 'Bruto' THEN preco_m2_usd END), 0)
        , 2) AS ratio_upgrading
    FROM metric_valorizacao
    GROUP BY ano_mes
    ORDER BY ano_mes
    """)

    logger.info("Valorização: monitor calculado")
