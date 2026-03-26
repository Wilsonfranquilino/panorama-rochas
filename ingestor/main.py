"""
Ingestor — Panorama Rochas Naturais
Coleta dados das 5 fontes e salva em Bronze (Parquet)
"""
import os
from pathlib import Path
import logging; logger = logging.getLogger(__name__)
import pandas as pd

from sources.comex import fetch_comex
from sources.ibge import fetch_ibge
from sources.bcb import fetch_bcb
from sources.anm import fetch_anm
from sources.centrorochas import fetch_centrorochas

BRONZE = Path(os.getenv("BRONZE_PATH", "/data/bronze"))

def salvar_bronze(df: pd.DataFrame, nome: str):
    pasta = BRONZE / nome
    pasta.mkdir(parents=True, exist_ok=True)
    ts = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
    caminho = pasta / f"{nome}_{ts}.parquet"
    df.to_parquet(caminho, index=False)
    logger.info(f"Bronze: {caminho} salvo ({len(df)} linhas)")

def main():
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s"); logger.info("=== Ingestor iniciado ===")

    fontes = [
        ("comex",        fetch_comex),
        ("ibge",         fetch_ibge),
        ("bcb",          fetch_bcb),
        ("anm",          fetch_anm),
        ("centrorochas", fetch_centrorochas),
    ]

    for nome, fn in fontes:
        try:
            df = fn()
            salvar_bronze(df, nome)
        except Exception as e:
            logger.error(f"Erro ao ingerir {nome}: {e}")

    logger.info("=== Ingestor concluído ===")

if __name__ == "__main__":
    main()
