"""Página Radar de Oportunidades."""
import streamlit as st
import plotly.express as px
from utils.db import query

def render():
    st.title("Radar de Oportunidades")
    st.markdown("""
    Score por mercado calculado a partir de: **tamanho do mercado importador** × 
    **crescimento projetado** × **gap de participação do Brasil** × **(1 - risco geopolítico)**
    """)

    radar = query("SELECT * FROM metric_radar_oportunidades ORDER BY score_oportunidade DESC")

    # Bubble chart
    fig = px.scatter(
        radar,
        x="crescimento_anual",
        y="mercado_bi_usd",
        size="score_oportunidade",
        color="status",
        text="pais",
        labels={
            "crescimento_anual": "Crescimento anual do mercado",
            "mercado_bi_usd": "Tamanho do mercado (US$ bi)",
            "status": "Status Brasil"
        },
        color_discrete_map={
            "Não explorado":    "#D85A30",
            "Subexplorado":     "#BA7517",
            "Em desenvolvimento": "#185FA5",
            "Maduro":           "#1D9E75",
        }
    )
    fig.update_traces(textposition="top center")
    st.plotly_chart(fig, use_container_width=True)

    # Tabela ranking
    st.subheader("Ranking de oportunidades")
    st.dataframe(
        radar[["pais", "score_oportunidade", "status", "mercado_bi_usd",
               "crescimento_anual", "participacao_brasil_bi", "risco_geopolitico"]],
        use_container_width=True
    )
