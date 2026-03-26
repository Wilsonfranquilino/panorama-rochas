"""
Silver → Gold
Agrega KPIs e métricas estratégicas no DuckDB
"""
import duckdb
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

def transform(silver: Path, gold: Path, con: duckdb.DuckDBPyConnection):
    gold.mkdir(parents=True, exist_ok=True)
    logger.info("Gold: iniciando agregações")

    # Verifica arquivos Silver disponíveis
    comex_ok = (silver / "comex.parquet").exists()
    bcb_ok   = (silver / "bcb.parquet").exists()
    cr_ok    = (silver / "centrorochas.parquet").exists()

    if not comex_ok:
        logger.error("Gold: comex.parquet não encontrado em Silver — abortando")
        raise FileNotFoundError(f"Arquivo não encontrado: {silver}/comex.parquet")

    # KPIs mensais de exportação com câmbio
    if bcb_ok:
        con.execute(f"""
        CREATE OR REPLACE TABLE gold_exportacoes AS
        SELECT
            c.ano, c.mes, c.ano_mes,
            c.pais_nome, c.pais_codigo, c.continente,
            c.ncm, c.ncm_desc, c.estado,
            SUM(c.fob_usd)  AS fob_usd,
            SUM(c.peso_kg)  AS peso_kg,
            COALESCE(AVG(b.cambio_medio), 5.5) AS cambio,
            SUM(c.fob_usd) * COALESCE(AVG(b.cambio_medio), 5.5) AS fob_brl
        FROM '{silver}/comex.parquet' c
        LEFT JOIN '{silver}/bcb.parquet' b ON c.ano_mes = b.ano_mes
        GROUP BY 1,2,3,4,5,6,7,8,9
        """)
    else:
        con.execute(f"""
        CREATE OR REPLACE TABLE gold_exportacoes AS
        SELECT
            ano, mes, ano_mes,
            pais_nome, pais_codigo, continente,
            ncm, ncm_desc, estado,
            SUM(fob_usd) AS fob_usd,
            SUM(peso_kg) AS peso_kg,
            5.5 AS cambio,
            SUM(fob_usd) * 5.5 AS fob_brl
        FROM '{silver}/comex.parquet'
        GROUP BY 1,2,3,4,5,6,7,8,9
        """)
    logger.info("Gold: exportacoes criado")

    # Totais anuais
    con.execute("""
    CREATE OR REPLACE TABLE gold_totais_anuais AS
    SELECT
        ano,
        SUM(fob_usd)  AS total_fob_usd,
        SUM(fob_brl)  AS total_fob_brl,
        SUM(peso_kg)  AS total_kg,
        COUNT(DISTINCT pais_codigo) AS num_paises,
        COUNT(DISTINCT ncm)         AS num_ncms,
        COUNT(DISTINCT estado)      AS num_estados
    FROM gold_exportacoes
    GROUP BY ano
    ORDER BY ano
    """)
    logger.info("Gold: totais_anuais criado")

    # Ranking de destinos por ano
    con.execute("""
    CREATE OR REPLACE TABLE gold_ranking_destinos AS
    SELECT
        ano, pais_nome, continente,
        SUM(fob_usd) AS fob_usd,
        ROUND(SUM(fob_usd) * 100.0 /
            SUM(SUM(fob_usd)) OVER (PARTITION BY ano), 2) AS pct_total,
        ROW_NUMBER() OVER (PARTITION BY ano ORDER BY SUM(fob_usd) DESC) AS rank
    FROM gold_exportacoes
    GROUP BY ano, pais_nome, continente
    """)
    logger.info("Gold: ranking_destinos criado")

    # Preço médio por produto (Centrorochas)
    if cr_ok:
        con.execute(f"""
        CREATE OR REPLACE TABLE gold_preco_produto AS
        SELECT
            ano_mes, produto,
            SUM(volume_m2)    AS volume_m2,
            SUM(fob_usd)      AS fob_usd,
            AVG(preco_m2_usd) AS preco_m2_usd
        FROM '{silver}/centrorochas.parquet'
        GROUP BY 1, 2
        ORDER BY 1, 2
        """)
        logger.info("Gold: preco_produto criado")
    else:
        logger.warning("Gold: centrorochas.parquet ausente — tabela preco_produto pulada")
        con.execute("""
        CREATE OR REPLACE TABLE gold_preco_produto AS
        SELECT NULL::VARCHAR AS ano_mes, NULL::VARCHAR AS produto,
               0.0 AS volume_m2, 0.0 AS fob_usd, 0.0 AS preco_m2_usd
        WHERE 1=0
        """)

    logger.info("Gold: todas as tabelas base criadas")
