"""
Transformer — Panorama Rochas Naturais
Bronze → Silver → Gold + Métricas estratégicas
"""
import os
import duckdb
from pathlib import Path
import logging; logger = logging.getLogger(__name__)

from layers.bronze_to_silver import transform as bronze_to_silver
from layers.silver_to_gold import transform as silver_to_gold
from metrics.ivm import calcular_ivm
from metrics.radar import calcular_radar
from metrics.valorizacao import calcular_valorizacao

BRONZE = Path(os.getenv("BRONZE_PATH", "/data/bronze"))
SILVER = Path(os.getenv("SILVER_PATH", "/data/silver"))
GOLD   = Path(os.getenv("GOLD_PATH",   "/data/gold"))

def main():
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s"); logger.info("=== Transformer iniciado ===")

    GOLD.mkdir(parents=True, exist_ok=True)
    db_path = str(GOLD / "panorama.duckdb")
    con = duckdb.connect(db_path)

    try:
        bronze_to_silver(BRONZE, SILVER, con)
        silver_to_gold(SILVER, GOLD, con)
        calcular_ivm(con)
        calcular_radar(con)
        calcular_valorizacao(con)
        con.execute("CHECKPOINT")
        logger.info(f"=== Transformer concluído → {db_path} ===")
    finally:
        con.close()

if __name__ == "__main__":
    main()
