"""
Métrica 2: Radar de Oportunidades
Score por país: tamanho do mercado × crescimento × gap Brasil × risco
"""
import duckdb
import logging; logger = logging.getLogger(__name__)

# Mercados de referência com potencial estimado (base pública + conhecimento setorial)
MERCADOS_REFERENCIA = [
    {"pais": "Índia",            "mercado_bi": 2.8, "crescimento": 0.12, "risco": 0.3},
    {"pais": "Emirados Árabes",  "mercado_bi": 1.9, "crescimento": 0.09, "risco": 0.2},
    {"pais": "Austrália",        "mercado_bi": 1.4, "crescimento": 0.07, "risco": 0.1},
    {"pais": "Canadá",           "mercado_bi": 1.2, "crescimento": 0.05, "risco": 0.1},
    {"pais": "Polônia",          "mercado_bi": 0.9, "crescimento": 0.08, "risco": 0.2},
    {"pais": "Japão",            "mercado_bi": 1.6, "crescimento": 0.03, "risco": 0.1},
    {"pais": "Coreia do Sul",    "mercado_bi": 0.8, "crescimento": 0.05, "risco": 0.1},
    {"pais": "Reino Unido",      "mercado_bi": 1.1, "crescimento": 0.04, "risco": 0.2},
    {"pais": "França",           "mercado_bi": 1.0, "crescimento": 0.03, "risco": 0.1},
    {"pais": "Arabia Saudita",   "mercado_bi": 1.5, "crescimento": 0.10, "risco": 0.3},
]

def calcular_radar(con: duckdb.DuckDBPyConnection):
    logger.info("Radar: calculando oportunidades de mercado")

    # Participação atual do Brasil em cada mercado (último ano disponível)
    con.execute("""
    CREATE OR REPLACE TABLE metric_participacao_atual AS
    SELECT
        pais_nome,
        SUM(fob_usd) AS fob_brasil_usd
    FROM gold_exportacoes
    WHERE ano = (SELECT MAX(ano) FROM gold_exportacoes)
    GROUP BY pais_nome
    """)

    # Monta tabela de referência de mercados
    mercados_vals = ",".join([
        f"('{m['pais']}', {m['mercado_bi']}, {m['crescimento']}, {m['risco']})"
        for m in MERCADOS_REFERENCIA
    ])

    con.execute(f"""
    CREATE OR REPLACE TABLE metric_radar_oportunidades AS
    WITH mercados AS (
        SELECT * FROM (VALUES {mercados_vals})
        AS t(pais, mercado_bi_usd, crescimento_anual, risco_geopolitico)
    ),
    atual AS (
        SELECT pais_nome, fob_brasil_usd
        FROM metric_participacao_atual
    )
    SELECT
        m.pais,
        m.mercado_bi_usd,
        m.crescimento_anual,
        m.risco_geopolitico,
        COALESCE(a.fob_brasil_usd, 0) / 1e9 AS participacao_brasil_bi,
        ROUND(
            (m.mercado_bi_usd * 0.4) *
            (1 + m.crescimento_anual * 0.3) *
            (1 - COALESCE(a.fob_brasil_usd,0) / NULLIF(m.mercado_bi_usd * 1e9, 0)) *
            (1 - m.risco_geopolitico * 0.3)
        , 3) AS score_oportunidade,
        CASE
            WHEN COALESCE(a.fob_brasil_usd, 0) = 0 THEN 'Não explorado'
            WHEN COALESCE(a.fob_brasil_usd, 0) / (m.mercado_bi_usd * 1e9) < 0.05 THEN 'Subexplorado'
            WHEN COALESCE(a.fob_brasil_usd, 0) / (m.mercado_bi_usd * 1e9) < 0.15 THEN 'Em desenvolvimento'
            ELSE 'Maduro'
        END AS status
    FROM mercados m
    LEFT JOIN atual a ON a.pais_nome ILIKE '%' || m.pais || '%'
    ORDER BY score_oportunidade DESC
    """)

    n = con.execute("SELECT COUNT(*) FROM metric_radar_oportunidades").fetchone()[0]
    logger.info(f"Radar: {n} mercados avaliados")
