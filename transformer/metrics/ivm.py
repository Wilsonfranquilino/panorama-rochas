"""
Métrica 1: IVM — Índice de Vulnerabilidade de Mercado
Combina HHI de destinos + HHI de produtos + sazonalidade
Escala 0 a 1 (quanto maior, mais vulnerável)
"""
import duckdb
import logging; logger = logging.getLogger(__name__)

def calcular_ivm(con: duckdb.DuckDBPyConnection):
    logger.info("IVM: calculando índice de vulnerabilidade")

    # HHI por destino (por ano) — Herfindahl-Hirschman Index
    con.execute("""
    CREATE OR REPLACE TABLE metric_hhi_destino AS
    WITH shares AS (
        SELECT
            ano,
            pais_nome,
            SUM(fob_usd) AS fob_pais,
            SUM(fob_usd) * 1.0 / SUM(SUM(fob_usd)) OVER (PARTITION BY ano) AS share
        FROM gold_exportacoes
        GROUP BY ano, pais_nome
    )
    SELECT
        ano,
        ROUND(SUM(share * share), 4) AS hhi_destino,
        COUNT(*) AS num_paises
    FROM shares
    GROUP BY ano
    """)

    # HHI por produto (por ano)
    con.execute("""
    CREATE OR REPLACE TABLE metric_hhi_produto AS
    WITH shares AS (
        SELECT
            ano,
            ncm_desc,
            SUM(fob_usd) AS fob_ncm,
            SUM(fob_usd) * 1.0 / SUM(SUM(fob_usd)) OVER (PARTITION BY ano) AS share
        FROM gold_exportacoes
        GROUP BY ano, ncm_desc
    )
    SELECT
        ano,
        ROUND(SUM(share * share), 4) AS hhi_produto
    FROM shares
    GROUP BY ano
    """)

    # Sazonalidade: desvio padrão dos meses (normalizado)
    con.execute("""
    CREATE OR REPLACE TABLE metric_sazonalidade AS
    WITH mensais AS (
        SELECT ano, mes, SUM(fob_usd) AS fob_mes
        FROM gold_exportacoes
        GROUP BY ano, mes
    )
    SELECT
        ano,
        ROUND(STDDEV(fob_mes) / NULLIF(AVG(fob_mes), 0), 4) AS coef_sazonalidade
    FROM mensais
    GROUP BY ano
    """)

    # IVM composto: média ponderada dos três componentes
    con.execute("""
    CREATE OR REPLACE TABLE metric_ivm AS
    SELECT
        d.ano,
        d.hhi_destino,
        p.hhi_produto,
        COALESCE(s.coef_sazonalidade, 0) AS sazonalidade,
        d.num_paises,
        ROUND(
            0.50 * d.hhi_destino +
            0.30 * p.hhi_produto +
            0.20 * LEAST(COALESCE(s.coef_sazonalidade, 0), 1.0)
        , 4) AS ivm,
        CASE
            WHEN (0.50 * d.hhi_destino + 0.30 * p.hhi_produto +
                  0.20 * LEAST(COALESCE(s.coef_sazonalidade,0),1.0)) >= 0.65
                THEN 'ALTO'
            WHEN (0.50 * d.hhi_destino + 0.30 * p.hhi_produto +
                  0.20 * LEAST(COALESCE(s.coef_sazonalidade,0),1.0)) >= 0.35
                THEN 'MÉDIO'
            ELSE 'BAIXO'
        END AS nivel_risco
    FROM metric_hhi_destino d
    JOIN metric_hhi_produto p ON d.ano = p.ano
    LEFT JOIN metric_sazonalidade s ON d.ano = s.ano
    ORDER BY d.ano
    """)

    n = con.execute("SELECT COUNT(*) FROM metric_ivm").fetchone()[0]
    logger.info(f"IVM: calculado para {n} anos")
