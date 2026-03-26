"""Página Home — visão geral do setor."""
import streamlit as st
import plotly.express as px
from utils.db import query

def render():
    st.title("Panorama das Rochas Naturais — Brasil")
    st.caption("Dados: COMEX Stat · IBGE · BCB · ANM · Centrorochas")

    # KPIs principais
    tot = query("SELECT * FROM gold_totais_anuais ORDER BY ano DESC LIMIT 2")
    if len(tot) >= 2:
        atual, ant = tot.iloc[0], tot.iloc[1]
        var = (atual["total_fob_usd"] - ant["total_fob_usd"]) / ant["total_fob_usd"] * 100

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Exportações", f"US$ {atual['total_fob_usd']/1e9:.2f}bi", f"{var:+.1f}%")
        c2.metric("Países destino", int(atual["num_paises"]))
        c3.metric("Ano", int(atual["ano"]))
        c4.metric("Estados exportadores", int(atual["num_estados"]))

    st.divider()

    # Série histórica
    st.subheader("Evolução das exportações")
    serie = query("SELECT ano, total_fob_usd/1e9 AS bi FROM gold_totais_anuais ORDER BY ano")
    fig = px.bar(serie, x="ano", y="bi",
                 labels={"bi": "US$ bilhões", "ano": ""},
                 color="bi", color_continuous_scale="teal")
    fig.update_layout(showlegend=False, coloraxis_showscale=False)
    st.plotly_chart(fig, use_container_width=True)

    # Ranking destinos
    st.subheader("Principais destinos (último ano)")
    rank = query("""
        SELECT pais_nome, fob_usd/1e6 AS fob_mi, pct_total, continente
        FROM gold_ranking_destinos
        WHERE ano = (SELECT MAX(ano) FROM gold_ranking_destinos)
        ORDER BY rank LIMIT 10
    """)
    fig2 = px.bar(rank, x="fob_usd_mi", y="pais_nome", orientation="h",
                  color="continente",
                  labels={"fob_usd_mi": "US$ milhões", "pais_nome": ""},
                  color_discrete_sequence=px.colors.qualitative.Set2)
    fig2.update_layout(yaxis={"categoryorder": "total ascending"})
    st.plotly_chart(fig2, use_container_width=True)
