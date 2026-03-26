"""Página Radar de Oportunidades."""
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from utils.db import query
 
def render():
    st.title("Radar de Oportunidades")
    st.markdown("""
    Score por mercado: **tamanho** × **crescimento** × **gap Brasil** × **(1 − risco)**
 
    Quanto maior o score, maior o potencial inexplorado pelo Brasil.
    """)
 
    radar = query("SELECT * FROM metric_radar_oportunidades ORDER BY score_oportunidade DESC")
 
    # Filtro por status
    status_opts = radar["status"].unique().tolist()
    status_sel  = st.multiselect("Filtrar por status", status_opts, default=status_opts)
    radar_f = radar[radar["status"].isin(status_sel)]
 
    # KPIs
    k1, k2, k3 = st.columns(3)
    k1.metric("Mercados analisados", len(radar_f))
    k2.metric("Não explorados",      (radar_f["status"] == "Não explorado").sum())
    k3.metric("Subexplorados",       (radar_f["status"] == "Subexplorado").sum())
 
    st.divider()
 
    cor_map = {
        "Não explorado":      "#D85A30",
        "Subexplorado":       "#BA7517",
        "Em desenvolvimento": "#185FA5",
        "Maduro":             "#1D9E75",
    }
 
    # Bubble chart
    st.subheader("Mapa de oportunidades")
    fig = px.scatter(
        radar_f,
        x="crescimento_anual", y="mercado_bi_usd",
        size="score_oportunidade", color="status", text="pais",
        labels={
            "crescimento_anual": "Crescimento anual do mercado",
            "mercado_bi_usd":    "Tamanho (US$ bi)",
            "status":            "Status Brasil"
        },
        color_discrete_map=cor_map,
        size_max=60
    )
    fig.update_traces(textposition="top center", textfont_size=12)
    fig.update_layout(xaxis_tickformat=".0%")
    st.plotly_chart(fig, use_container_width=True)
 
    # Ranking score
    st.subheader("Ranking de score de oportunidade")
    fig2 = px.bar(radar_f.sort_values("score_oportunidade"),
                  x="score_oportunidade", y="pais", orientation="h",
                  color="status", color_discrete_map=cor_map,
                  labels={"score_oportunidade":"Score","pais":"País"})
    st.plotly_chart(fig2, use_container_width=True)
 
    # Gap participação atual vs potencial
    st.subheader("Gap: participação atual vs potencial estimado")
    radar_f2 = radar_f.copy()
    radar_f2["potencial_estimado_bi"] = radar_f2["mercado_bi_usd"] * 0.08
    fig3 = go.Figure()
    fig3.add_trace(go.Bar(
        name="Participação atual BR (US$ bi)",
        x=radar_f2["pais"], y=radar_f2["participacao_brasil_bi"],
        marker_color="#85B7EB"
    ))
    fig3.add_trace(go.Bar(
        name="Potencial estimado (US$ bi)",
        x=radar_f2["pais"], y=radar_f2["potencial_estimado_bi"],
        marker_color="#D85A30", opacity=0.6
    ))
    fig3.update_layout(
        barmode="overlay", xaxis_tickangle=-30,
        yaxis_title="US$ bilhões",
        legend=dict(orientation="h", y=-0.25)
    )
    st.plotly_chart(fig3, use_container_width=True)
 
    # Tabela
    st.subheader("Dados completos")
    cols = ["pais","score_oportunidade","status","mercado_bi_usd",
            "crescimento_anual","participacao_brasil_bi","risco_geopolitico"]
    st.dataframe(radar_f[cols], use_container_width=True, hide_index=True)