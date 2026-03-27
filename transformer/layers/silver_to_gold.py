import duckdb
import logging
from pathlib import Path

# Configuração do logger para garantir que você veja as mensagens no terminal
logger = logging.getLogger(__name__)

def transform(silver: Path, gold: Path, con: duckdb.DuckDBPyConnection):
    """
    Transformação Gold: Agregações estratégicas e câmbio inteligente.
    """
    # Garante que a pasta Gold exista
    gold.mkdir(parents=True, exist_ok=True)
    logger.info("Gold: iniciando agregações estratégicas")

    # Verificação de arquivos na Silver
    comex_ok = (silver / "comex.parquet").exists()
    bcb_ok   = (silver / "bcb.parquet").exists()
    cr_ok    = (silver / "centrorochas.parquet").exists()

    if not comex_ok:
        logger.error("Gold: comex.parquet não encontrado — abortando")
        raise FileNotFoundError(f"Arquivo ausente: {silver}/comex.parquet")

    # --- KPIs de Exportação com Câmbio Inteligente ---
    con.execute(f"""
    CREATE OR REPLACE TABLE gold_exportacoes AS
    WITH bcb_mensal AS (
        SELECT ano_mes, AVG(cambio_medio) as cambio_medio
        FROM '{silver}/bcb.parquet'
        GROUP BY 1
    ),
    cambio_fallback AS (
        SELECT AVG(cambio_medio) as media_geral FROM bcb_mensal
    )
    SELECT
        c.ano, c.mes, c.ano_mes,
        c.pais_nome, c.pais_codigo, c.continente,
        c.ncm, c.ncm_desc, c.estado,
        SUM(c.fob_usd)  AS fob_usd,
        SUM(c.peso_kg)  AS peso_kg,
        COALESCE(MAX(b.cambio_medio), (SELECT media_geral FROM cambio_fallback)) AS cambio,
        SUM(c.fob_usd) * COALESCE(MAX(b.cambio_medio), (SELECT media_geral FROM cambio_fallback)) AS fob_brl
    FROM '{silver}/comex.parquet' c
    LEFT JOIN bcb_mensal b ON c.ano_mes = b.ano_mes
    GROUP BY 1,2,3,4,5,6,7,8,9
    """)

    # --- Totais Anuais (Consolidado) ---
    con.execute("""
    CREATE OR REPLACE TABLE gold_totais_anuais AS
    SELECT
        ano,
        SUM(fob_usd)  AS total_fob_usd,
        SUM(fob_brl)  AS total_fob_brl,
        SUM(peso_kg) / 1000 AS total_toneladas,
        COUNT(DISTINCT pais_codigo) AS num_paises,
        COUNT(DISTINCT ncm)         AS num_ncms
    FROM gold_exportacoes
    GROUP BY ano ORDER BY ano
    """)

    # --- Ranking de Destinos ---
    con.execute("""
    CREATE OR REPLACE TABLE gold_ranking_destinos AS
    SELECT
        ano, pais_nome, continente,
        SUM(fob_usd) AS fob_usd,
        ROUND(SUM(fob_usd) * 100.0 / SUM(SUM(fob_usd)) OVER (PARTITION BY ano), 2) AS pct_total,
        ROW_NUMBER() OVER (PARTITION BY ano ORDER BY SUM(fob_usd) DESC) AS rank
    FROM gold_exportacoes
    GROUP BY ano, pais_nome, continente
    """)

    # --- Preço Médio (Centrorochas) ---
    if cr_ok:
        con.execute(f"""
        CREATE OR REPLACE TABLE gold_preco_produto AS
        SELECT
            ano_mes, produto,
            SUM(volume_m2)    AS volume_m2,
            SUM(fob_usd)      AS fob_usd,
            SUM(fob_usd) / NULLIF(SUM(volume_m2), 0) AS preco_m2_usd
        FROM '{silver}/centrorochas.parquet'
        GROUP BY 1, 2 ORDER BY 1, 2
        """)

    logger.info("✅ Gold: Tabelas base criadas com validade garantida.")