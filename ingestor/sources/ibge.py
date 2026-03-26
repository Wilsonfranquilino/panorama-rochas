"""
Fonte 2: IBGE SIDRA
Tabela 2612: Produção industrial mineral
Tabela 8159: Empregos no setor de extração
"""
import requests
import pandas as pd
import logging; logger = logging.getLogger(__name__)

def fetch_ibge() -> pd.DataFrame:
    """Busca dados de produção e emprego mineral do IBGE SIDRA."""
    logger.info("IBGE SIDRA: buscando produção industrial mineral")
    
    # Tabela 8159 - Pesquisa Industrial Anual
    url = "https://apisidra.ibge.gov.br/values/t/8159/n1/all/v/all/p/all/c544/all"
    
    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        df = pd.DataFrame(data[1:], columns=data[0].keys() if data else [])
        df["source"] = "ibge"
        df["ingested_at"] = pd.Timestamp.now()
        logger.info(f"IBGE: {len(df)} registros coletados")
        return df
    except Exception as e:
        logger.warning(f"IBGE API indisponível ({e}), usando dados simulados")
        return _mock_ibge()

def _mock_ibge() -> pd.DataFrame:
    """Dados simulados de produção mineral para POC."""
    anos = range(2018, 2026)
    rows = []
    for ano in anos:
        rows.append({
            "ano": ano,
            "producao_ton": 180_000 + (ano - 2018) * 8_000,
            "empregos_diretos": 95_000 + (ano - 2018) * 1_200,
            "valor_producao_brl": 4_200_000_000 + (ano - 2018) * 350_000_000,
            "source": "ibge",
            "ingested_at": pd.Timestamp.now(),
        })
    return pd.DataFrame(rows)
