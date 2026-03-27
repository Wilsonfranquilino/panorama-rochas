import duckdb
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

def transform(bronze: Path, silver: Path, con: duckdb.DuckDBPyConnection):
    silver.mkdir(parents=True, exist_ok=True)
    logger.info("Silver: iniciando transformações com Cura Autônoma")

    # --- 1. COMEX: Carga Inicial ---
    comex_files = list((bronze / "comex").glob("*.parquet"))
    if comex_files:
        # Note que removi o SELECT DISTINCT para não perdermos valores legítimos iguais
        con.execute(f"""
        CREATE OR REPLACE TABLE silver_comex AS
        SELECT 
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
        WHERE ncmCode IS NOT NULL AND metricFOB > 0 AND metricKG > 0
        """)

        # --- 2. CURA AUTÔNOMA (O Coração da Validade) ---
        # Calculamos a média e o desvio por NCM para identificar o "Preço Justo"
        con.execute("""
            CREATE OR REPLACE TEMP TABLE stats_precos AS
            SELECT 
                ncm,
                AVG(fob_usd / peso_kg) AS preco_medio_kg,
                STDDEV(fob_usd / peso_kg) AS desvio_padrao
            FROM silver_comex
            GROUP BY ncm
        """)

        # Se o preço/kg estiver fora de 3 desvios padrão (erro crasso), 
        # ele é forçado para a média (Preço Médio * Peso Real)
        con.execute("""
            UPDATE silver_comex
            SET fob_usd = s.preco_medio_kg * silver_comex.peso_kg
            FROM stats_precos s
            WHERE silver_comex.ncm = s.ncm
              AND s.desvio_padrao IS NOT NULL
              AND (
                  (fob_usd / peso_kg) > (s.preco_medio_kg + 3 * s.desvio_padrao)
                  OR 
                  (fob_usd / peso_kg) < (s.preco_medio_kg - 3 * s.desvio_padrao)
              )
        """)
        
        # Salva o arquivo já "curado"
        con.execute(f"COPY silver_comex TO '{silver}/comex.parquet' (FORMAT PARQUET)")
        n = con.execute("SELECT COUNT(*) FROM silver_comex").fetchone()[0]
        logger.info(f"Silver COMEX: {n} registros curados e salvos")

    # --- 3. BCB: Câmbio Mensal Médio ---
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

    # --- 4. ANM: Produção (Ajustado para SUM no IBGE/ANM conforme sua necessidade) ---
    anm_files = list((bronze / "anm").glob("*.parquet"))
    if anm_files:
        con.execute(f"""
        CREATE OR REPLACE TABLE silver_anm AS
        SELECT
            CAST(ano AS INTEGER)              AS ano,
            substancia,
            SUM(CAST(producao_ton AS DOUBLE)) AS producao_ton,
            SUM(CAST(valor_brl    AS DOUBLE)) AS valor_brl,
            AVG(CAST(preco_medio_ton AS DOUBLE)) AS preco_medio_ton
        FROM read_parquet('{bronze}/anm/*.parquet')
        GROUP BY 1, 2
        """)
        con.execute(f"COPY silver_anm TO '{silver}/anm.parquet' (FORMAT PARQUET)")

    # (O restante do código do IBGE e Centrorochas segue a mesma lógica de salvamento)
    # ... [Manter lógica anterior para IBGE e Centrorochas] ...

    logger.info("Silver: todas as transformações e cura concluídas")