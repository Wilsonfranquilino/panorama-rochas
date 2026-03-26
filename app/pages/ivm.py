"""Página IVM — Índice de Vulnerabilidade de Mercado."""
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from utils.db import query

def render():
    st.title("Índice de Vulnerabilidade de Mercado (IVM)")
    st.markdown("""
    O IVM combina três dimensões para medir o risco estrutural das exportações:
    - **50%** HHI de concentração por destino geográfico
    - **30%** HHI de concentração por produto (NCM)
    - **20%** Sazonalidade da receita ao longo do ano
    
    Escala: **0** (diversificado, baixo risco) → **1** (concentrado, alto risco)
    """)

    ivm = query("SELECT * FROM metric_ivm ORDER BY ano")
    ultimo = ivm.iloc[-1]

    # Gauge do IVM atual
    fig_gauge = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=float(ultimo["ivm"]),
        delta={"reference": float(ivm.iloc[-2]["ivm"]) if len(ivm) > 1 else 0},
        title={"text": f"IVM {int(ultimo['ano'])} — Risco {ultimo['nivel_risco']}"},
        gauge={
            "axis": {"range": [0, 1]},
            "bar": {"color": "#D85A30"},
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
    st.subheader("Evolução do IVM")
    fig = px.line(ivm, x="ano", y=["hhi_destino", "hhi_produto", "ivm"],
                  labels={"value": "Índice", "variable": "Componente", "ano": ""},
                  color_discrete_map={"ivm": "#D85A30", "hhi_destino": "#185FA5", "hhi_produto": "#1D9E75"})
    st.plotly_chart(fig, use_container_width=True)

    # Tabela detalhada
    st.subheader("Dados por ano")
    st.dataframe(
        ivm[["ano", "hhi_destino", "hhi_produto", "sazonalidade", "ivm", "nivel_risco", "num_paises"]],
        use_container_width=True
    )

    # Benchmark
    st.info("""
    **Referência internacional:** Itália IVM ≈ 0.28 · China IVM ≈ 0.31
    
    Um IVM acima de **0.65** indica concentração crítica — qualquer mudança num único mercado 
    (tarifas, crise, câmbio) impacta fortemente o setor inteiro.
    """)
