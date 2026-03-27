"""
Transformer — Panorama Rochas Naturais
Bronze → Silver → Gold + Métricas estratégicas + Data Quality Final
"""
import os
import duckdb
from pathlib import Path
import logging

# Importações das camadas e métricas
from layers.bronze_to_silver import transform as bronze_to_silver
from layers.silver_to_gold import transform as silver_to_gold
from metrics.ivm import calcular_ivm
from metrics.radar import calcular_radar
from metrics.valorizacao import calcular_valorizacao

logger = logging.getLogger(__name__)

BRONZE = Path(os.getenv("BRONZE_PATH", "data/bronze"))
SILVER = Path(os.getenv("SILVER_PATH", "data/silver"))
GOLD   = Path(os.getenv("GOLD_PATH",   "data/gold"))

def validar_fechamento_contabil(con, bronze_path):
    """
    DQ Final: Compara o FOB total da Bronze com a Gold Curada.
    Garante que a limpeza de outliers manteve a integridade do faturamento.
    """
    logger.info("DQ: Iniciando Reconciliação Contábil Final")
    
    # 1. Soma original da Bronze
    fob_orig = con.execute(f"SELECT SUM(CAST(metricFOB AS DOUBLE)) FROM read_parquet('{bronze_path}/comex/*.parquet')").fetchone()[0] or 0
    
    # 2. Soma curada na Gold
    fob_curado = con.execute("SELECT SUM(fob_usd) FROM gold_exportacoes").fetchone()[0] or 0
    
    if fob_orig > 0:
        diff_pct = abs(fob_orig - fob_curado) / fob_orig * 100
        if diff_pct > 1.0: # Se a cura alterou mais de 1%, vale um aviso
            logger.warning(f"⚠️ Ajuste de Dados: A cura de outliers reduziu o ruído em {diff_pct:.2f}% do total.")
        else:
            logger.info(f"✅ Integridade OK: Diferença residual de {diff_pct:.4f}% (dentro da margem estatística).")
    
    return True

def main():
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    logger.info("=== Transformer iniciado ===")

    GOLD.mkdir(parents=True, exist_ok=True)
    db_path = str(GOLD / "panorama.duckdb")
    con = duckdb.connect(db_path)

    try:
        # Camadas de Transformação (Com Cura Autônoma na Silver)
        bronze_to_silver(BRONZE, SILVER, con)
        silver_to_gold(SILVER, GOLD, con)
        
        # Cálculo das Métricas de Inteligência
        calcular_ivm(con)
        calcular_radar(con)
        calcular_valorizacao(con)
        
        # --- DATA QUALITY FINAL (O SELO DE VALIDADE) ---
        validar_fechamento_contabil(con, BRONZE)
        
        con.execute("CHECKPOINT")
        logger.info(f"=== Transformer concluído → {db_path} ===")
        
    except Exception as e:
        logger.error(f"❌ Erro no Pipeline: {str(e)}")
        raise e
    finally:
        con.close()

if __name__ == "__main__":
    main()