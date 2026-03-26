"""Página IVM — Índice de Vulnerabilidade de Mercado."""
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from utils.db import query
 
def render():
    st.title("Índice de Vulnerabilidade de Mercado (IVM)")
    st.markdown("""
    O IVM combina três dimensões para medir o **risco estrutural** das exportações:
    - **50%** Concentração geográfica (HHI de destinos)
    - **30%** Concentração de produto (HHI por NCM)
    - **20%** Sazonalidade da receita
 
    Escala: **0** = diversificado, baixo risco → **1** = concentrado, alto risco
    """)
 
    ivm    = query("SELECT * FROM metric_ivm ORDER BY ano")
    ultimo = ivm.iloc[-1]
 
    cor_gauge = {"ALTO": "#D85A30", "MÉDIO": "#BA7517", "BAIXO": "#1D9E75"}
 
    # Gauge
    fig_gauge = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=float(ultimo["ivm"]),
        delta={"reference": float(ivm.iloc[-2]["ivm"]) if len(ivm) > 1 else 0,
               "valueformat": ".4f"},
        title={"text": f"IVM {int(ultimo['ano'])} — Risco {ultimo['nivel_risco']}"},
        gauge={
            "axis": {"range": [0, 1], "tickformat": ".2f"},
            "bar":  {"color": cor_gauge.get(ultimo["nivel_risco"], "#185FA5")},
            "steps": [
                {"range": [0.00, 0.35], "color": "#E1F5EE"},
                {"range": [0.35, 0.65], "color": "#FAEEDA"},
                {"range": [0.65, 1.00], "color": "#FAECE7"},
            ],
            "threshold": {"line": {"color": "red", "width": 3}, "value": 0.65}
        }
    ))
    st.plotly_chart(fig_gauge, use_container_width=True)
 
    # Evolução histórica
    st.subheader("Evolução histórica dos componentes")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=ivm["ano"], y=ivm["ivm"], name="IVM Total",
                             line=dict(color="#D85A30", width=3), mode="lines+markers"))
    fig.add_trace(go.Scatter(x=ivm["ano"], y=ivm["hhi_destino"], name="HHI Destino",
                             line=dict(color="#185FA5", dash="dash")))
    fig.add_trace(go.Scatter(x=ivm["ano"], y=ivm["hhi_produto"], name="HHI Produto",
                             line=dict(color="#1D9E75", dash="dot")))
    fig.add_hrect(y0=0.65, y1=1.0, fillcolor="#FAECE7", opacity=0.3,
                  annotation_text="Risco alto", annotation_position="top left")
    fig.add_hrect(y0=0.35, y1=0.65, fillcolor="#FAEEDA", opacity=0.2,
                  annotation_text="Risco médio", annotation_position="top left")
    fig.update_layout(yaxis_title="Índice", xaxis_title="Ano",
                      legend=dict(orientation="h", y=-0.2))
    st.plotly_chart(fig, use_container_width=True)
 
    # Concentração por destino
    st.subheader(f"Concentração por destino — {int(ultimo['ano'])}")
    rank = query(f"""
        SELECT pais_nome, continente, fob_usd, pct_total
        FROM gold_ranking_destinos
        WHERE ano = {int(ultimo['ano'])}
        ORDER BY rank
    """)
 
    col1, col2 = st.columns(2)
    with col1:
        fig_tree = px.treemap(rank.head(12),
                              path=["continente","pais_nome"],
                              values="fob_usd",
                              color="pct_total",
                              color_continuous_scale="Blues",
                              labels={"pct_total":"% do total"})
        st.plotly_chart(fig_tree, use_container_width=True)
    with col2:
        fig_pie = px.pie(rank.head(8), values="fob_usd", names="pais_nome",
                         hole=0.45,
                         color_discrete_sequence=px.colors.qualitative.Set2)
        fig_pie.update_traces(textposition="inside", textinfo="percent+label")
        st.plotly_chart(fig_pie, use_container_width=True)
 
    st.info("""
    **Benchmarks internacionais:** Itália ≈ 0.28 · China ≈ 0.31 · Espanha ≈ 0.33
 
    IVM acima de **0.65** = concentração crítica.
    Meta estratégica sugerida: **abaixo de 0.40** até 2030.
    """)
 
    st.subheader("Dados por ano")
    st.dataframe(
        ivm[["ano","hhi_destino","hhi_produto","sazonalidade","ivm","nivel_risco","num_paises"]],
        use_container_width=True, hide_index=True
    )