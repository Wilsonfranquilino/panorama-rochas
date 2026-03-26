"""
Bronze → Silver
Limpa, filtra e une as fontes em tabelas analíticas
"""
import duckdb
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

def transform(bronze: Path, silver: Path, con: duckdb.DuckDBPyConnection):
    silver.mkdir(parents=True, exist_ok=True)
    logger.info("Silver: iniciando transformações")

    # --- COMEX: filtrar NCMs de rochas + dedup ---
    comex_files = list((bronze / "comex").glob("*.parquet"))
    if comex_files:
        con.execute(f"""
        CREATE OR REPLACE TABLE silver_comex AS
        SELECT DISTINCT
            CAST(year AS INTEGER)  AS ano,
            CAST(month AS INTEGER) AS mes,
            CAST(year AS VARCHAR) || '-' || LPAD(CAST(month AS VARCHAR),2,'0') AS ano_mes,
            countryCode            AS pais_codigo,
            countryName            AS pais_nome,
            continent              AS continente,
            ncmCode                AS ncm,
            ncmDesc                AS ncm_desc,
            state                  AS estado,
            CAST(metricFOB AS DOUBLE) AS fob_usd,
            CAST(metricKG  AS DOUBLE) AS peso_kg
        FROM read_parquet('{bronze}/comex/*.parquet')
        WHERE ncmCode IS NOT NULL
          AND metricFOB > 0
        """)
        con.execute(f"COPY silver_comex TO '{silver}/comex.parquet' (FORMAT PARQUET)")
        n = con.execute("SELECT COUNT(*) FROM silver_comex").fetchone()[0]
        logger.info(f"Silver COMEX: {n} registros")

    # --- BCB: câmbio mensal médio ---
    bcb_files = list((bronze / "bcb").glob("*.parquet"))
    if bcb_files:
        con.execute(f"""
        CREATE OR REPLACE TABLE silver_bcb AS
        SELECT
            STRFTIME(CAST(data AS DATE), '%Y-%m') AS ano_mes,
            AVG(CAST(usd_brl AS DOUBLE))          AS cambio_medio
        FROM read_parquet('{bronze}/bcb/*.parquet')
        GROUP BY 1
        """)
        con.execute(f"COPY silver_bcb TO '{silver}/bcb.parquet' (FORMAT PARQUET)")
        logger.info("Silver BCB: câmbio mensal calculado")

    # --- ANM: produção por substância ---
    anm_files = list((bronze / "anm").glob("*.parquet"))
    if anm_files:
        con.execute(f"""
        CREATE OR REPLACE TABLE silver_anm AS
        SELECT
            CAST(ano AS INTEGER)             AS ano,
            substancia,
            SUM(CAST(producao_ton AS DOUBLE)) AS producao_ton,
            SUM(CAST(valor_brl    AS DOUBLE)) AS valor_brl,
            AVG(CAST(preco_medio_ton AS DOUBLE)) AS preco_medio_ton
        FROM read_parquet('{bronze}/anm/*.parquet')
        GROUP BY 1, 2
        """)
        con.execute(f"COPY silver_anm TO '{silver}/anm.parquet' (FORMAT PARQUET)")
        logger.info("Silver ANM: produção mineral consolidada")

    # --- IBGE: inspeciona colunas reais antes de processar ---
    ibge_files = list((bronze / "ibge").glob("*.parquet"))
    if ibge_files:
        try:
            cols_df = con.execute(
                f"DESCRIBE SELECT * FROM read_parquet('{bronze}/ibge/*.parquet') LIMIT 1"
            ).df()
            colunas_reais = cols_df["column_name"].tolist()
            logger.info(f"Silver IBGE: colunas reais = {colunas_reais}")

            if "ano" in colunas_reais:
                # Dados do mock
                con.execute(f"""
                CREATE OR REPLACE TABLE silver_ibge AS
                SELECT
                    CAST(ano AS INTEGER)                    AS ano,
                    AVG(CAST(producao_ton AS DOUBLE))       AS producao_ton,
                    AVG(CAST(empregos_diretos AS DOUBLE))   AS empregos_diretos,
                    AVG(CAST(valor_producao_brl AS DOUBLE)) AS valor_producao_brl
                FROM read_parquet('{bronze}/ibge/*.parquet')
                GROUP BY 1
                """)
            else:
                # Dados reais SIDRA — colunas NC, NN, MN, V, D1N, D1C, D2N, D2C...
                # D1N = período (ex: "2024"), V = valor numérico
                con.execute(f"""
                CREATE OR REPLACE TABLE silver_ibge AS
                SELECT
                    TRY_CAST(SUBSTRING("D1N", 1, 4) AS INTEGER) AS ano,
                    COUNT(*) AS num_registros,
                    SUM(TRY_CAST("V" AS DOUBLE)) AS valor_total
                FROM read_parquet('{bronze}/ibge/*.parquet')
                WHERE TRY_CAST("V" AS DOUBLE) IS NOT NULL
                GROUP BY 1
                HAVING ano IS NOT NULL
                ORDER BY 1
                """)

            con.execute(f"COPY silver_ibge TO '{silver}/ibge.parquet' (FORMAT PARQUET)")
            logger.info("Silver IBGE: processado com sucesso")
        except Exception as e:
            logger.warning(f"Silver IBGE: erro ao processar ({e}) — tabela pulada")

    # --- Centrorochas: preço por m² ---
    cr_files = list((bronze / "centrorochas").glob("*.parquet"))
    if cr_files:
        con.execute(f"""
        CREATE OR REPLACE TABLE silver_centrorochas AS
        SELECT
            mes                               AS ano_mes,
            produto,
            SUM(CAST(volume_m2    AS DOUBLE)) AS volume_m2,
            SUM(CAST(fob_usd      AS DOUBLE)) AS fob_usd,
            AVG(CAST(preco_m2_usd AS DOUBLE)) AS preco_m2_usd
        FROM read_parquet('{bronze}/centrorochas/*.parquet')
        GROUP BY 1, 2
        """)
        con.execute(f"COPY silver_centrorochas TO '{silver}/centrorochas.parquet' (FORMAT PARQUET)")
        logger.info("Silver Centrorochas: preço por m² consolidado")

    logger.info("Silver: todas as transformações concluídas")
