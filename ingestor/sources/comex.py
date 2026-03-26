"""
Fonte 1: COMEX Stat (MDIC)
NCMs capítulo 68 — rochas naturais: 6801, 6802, 6803, 6804, 6809, 6810
"""
import requests
import pandas as pd
import logging

logger = logging.getLogger(__name__)

NCM_PREFIXOS = ("6801", "6802", "6803", "6804", "6809", "6810")

def fetch_comex(ano_inicio: int = 2018) -> pd.DataFrame:
    """Busca exportações brasileiras de rochas naturais por NCM."""
    logger.info(f"COMEX Stat: buscando exportações NCM rochas desde {ano_inicio}")

    # Tenta diferentes endpoints da API COMEX
    endpoints = [
        {
            "url": "https://api-comexstat.mdic.gov.br/general",
            "payload": {
                "flow": "export",
                "monthDetail": True,
                "period": {"from": f"{ano_inicio}01", "to": "202512"},
                "filters": [{"filter": "chapter", "values": ["68"]}],
                "details": ["country", "state", "ncm"],
                "metrics": ["metricFOB", "metricKG"]
            }
        },
        {
            "url": "https://api-comexstat.mdic.gov.br/general",
            "payload": {
                "flow": "export",
                "monthDetail": True,
                "period": {"from": f"{ano_inicio}01", "to": "202512"},
                "details": ["country", "state", "ncm"],
                "metrics": ["metricFOB", "metricKG"],
                "filters": [{"filter": "ncm", "values": list(NCM_PREFIXOS)}]
            }
        }
    ]

    for ep in endpoints:
        try:
            resp = requests.post(ep["url"], json=ep["payload"], timeout=60)
            resp.raise_for_status()
            data = resp.json()
            registros = data.get("data", {}).get("list", [])
            if registros:
                df = pd.DataFrame(registros)
                df = df[df["ncmCode"].astype(str).str.startswith(NCM_PREFIXOS)]
                df["source"] = "comex"
                df["ingested_at"] = pd.Timestamp.now()
                logger.info(f"COMEX: {len(df)} registros coletados via API")
                return df
        except Exception as e:
            logger.warning(f"COMEX endpoint falhou ({e})")

    logger.warning("COMEX: todas as tentativas falharam, usando dados simulados")
    return _mock_comex(ano_inicio)


def _mock_comex(ano_inicio: int) -> pd.DataFrame:
    """Dados simulados realistas para desenvolvimento/POC."""
    import numpy as np

    anos = range(ano_inicio, 2026)
    meses = range(1, 13)
    paises = [
        {"code": "249", "name": "Estados Unidos", "continent": "América do Norte"},
        {"code": "160", "name": "China",           "continent": "Ásia"},
        {"code": "105", "name": "Itália",           "continent": "Europa"},
        {"code": "170", "name": "México",           "continent": "América Latina"},
        {"code": "245", "name": "Espanha",          "continent": "Europa"},
        {"code": "074", "name": "Alemanha",         "continent": "Europa"},
        {"code": "119", "name": "Índia",            "continent": "Ásia"},
        {"code": "031", "name": "Canadá",           "continent": "América do Norte"},
    ]
    ncms = [
        {"code": "68021000", "desc": "Granito bruto"},
        {"code": "68022100", "desc": "Mármore beneficiado"},
        {"code": "68029000", "desc": "Quartzito beneficiado"},
        {"code": "68010000", "desc": "Pedras naturais bruto"},
    ]
    estados = ["ES", "MG", "CE", "BA", "GO"]

    fob_base_map = {
        "249": 60_000_000, "160": 18_000_000,
        "105": 9_000_000,  "170": 5_000_000,
        "245": 4_000_000,  "074": 3_500_000,
        "119": 2_000_000,  "031": 1_500_000,
    }

    rows = []
    np.random.seed(42)
    for ano in anos:
        for mes in meses:
            for pais in paises:
                for ncm in ncms:
                    fob_base = fob_base_map[pais["code"]]
                    trend = 1 + (ano - ano_inicio) * 0.04
                    saz = 1 + 0.15 * np.sin((mes - 3) * np.pi / 6)
                    noise = np.random.uniform(0.85, 1.15)
                    rows.append({
                        "year": ano, "month": mes,
                        "countryCode": pais["code"],
                        "countryName": pais["name"],
                        "continent": pais["continent"],
                        "ncmCode": ncm["code"],
                        "ncmDesc": ncm["desc"],
                        "state": np.random.choice(estados),
                        "metricFOB": round(fob_base * trend * saz * noise / len(ncms)),
                        "metricKG":  round(fob_base * trend * saz * noise / len(ncms) * 45),
                        "source": "comex",
                        "ingested_at": pd.Timestamp.now(),
                    })

    logger.info(f"COMEX mock: {len(rows)} registros gerados")
    return pd.DataFrame(rows)
