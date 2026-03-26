"""
Fonte 5: Centrorochas / ABIROCHAS
Extração de dados de boletins PDF mensais via pdfplumber
"""
import requests
import pandas as pd
import pdfplumber
import io
import logging; logger = logging.getLogger(__name__)

BOLETINS = [
    {"url": "https://www.centrorochas.com.br/boletim-export-jan2025.pdf", "mes": "2025-01"},
    {"url": "https://www.centrorochas.com.br/boletim-export-dez2024.pdf", "mes": "2024-12"},
]

def fetch_centrorochas() -> pd.DataFrame:
    """Tenta extrair tabelas dos boletins PDF da Centrorochas."""
    logger.info("Centrorochas: tentando extrair boletins PDF")
    
    dfs = []
    for boletim in BOLETINS:
        try:
            resp = requests.get(boletim["url"], timeout=20)
            resp.raise_for_status()
            df = _parse_pdf(resp.content, boletim["mes"])
            dfs.append(df)
        except Exception as e:
            logger.warning(f"PDF {boletim['mes']} indisponível ({e})")
    
    if dfs:
        return pd.concat(dfs, ignore_index=True)
    
    logger.warning("Centrorochas: usando dados simulados")
    return _mock_centrorochas()

def _parse_pdf(content: bytes, mes: str) -> pd.DataFrame:
    """Extrai tabelas de um PDF da Centrorochas."""
    rows = []
    with pdfplumber.open(io.BytesIO(content)) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()
            for table in tables:
                for row in table[1:]:
                    if row and len(row) >= 4:
                        rows.append({
                            "mes": mes,
                            "produto": row[0],
                            "fob_usd": row[1],
                            "volume_m2": row[2],
                            "preco_m2_usd": row[3],
                            "source": "centrorochas",
                            "ingested_at": pd.Timestamp.now(),
                        })
    return pd.DataFrame(rows)

def _mock_centrorochas() -> pd.DataFrame:
    """Dados simulados de boletins Centrorochas."""
    meses = pd.date_range("2018-01", "2025-12", freq="MS").strftime("%Y-%m")
    produtos = [
        {"nome": "Granito bruto",        "preco_base": 42.0,  "vol_base": 1_800_000},
        {"nome": "Granito beneficiado",   "preco_base": 118.0, "vol_base":   420_000},
        {"nome": "Mármore beneficiado",   "preco_base": 145.0, "vol_base":   180_000},
        {"nome": "Quartzito beneficiado", "preco_base": 135.0, "vol_base":    95_000},
        {"nome": "Ardósia",              "preco_base": 98.0,  "vol_base":    42_000},
    ]
    
    rows = []
    for mes in meses:
        for p in produtos:
            trend = 1 + (int(mes[:4]) - 2018) * 0.05
            rows.append({
                "mes": mes,
                "produto": p["nome"],
                "volume_m2": round(p["vol_base"] * trend),
                "preco_m2_usd": round(p["preco_base"] * trend, 2),
                "fob_usd": round(p["vol_base"] * trend * p["preco_base"] * trend),
                "source": "centrorochas",
                "ingested_at": pd.Timestamp.now(),
            })
    return pd.DataFrame(rows)
