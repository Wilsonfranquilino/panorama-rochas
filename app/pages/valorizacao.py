"""Página Monitor de Valorização."""
import streamlit as st
import plotly.express as px
from utils.db import query

def render():
    st.title("Monitor de Valorização do Produto")
    st.markdown("""
    Acompanha a evolução do **preço médio por m²** por tipo de produto.
    A razão *beneficiado/bruto* indica o grau de upgrading do setor ao longo do tempo.
    """)

    val = query("SELECT * FROM metric_valorizacao ORDER BY ano_mes")
    ratio = query("SELECT * FROM metric_upgrading_ratio ORDER BY ano_mes")

    # Preço por produto
    produtos = val["produto"].unique().tolist()
    selecionados = st.multiselect("Produtos", produtos, default=produtos[:3])
    filtrado = val[val["produto"].isin(selecionados)]

    fig = px.line(filtrado, x="ano_mes", y="preco_m2_usd", color="produto",
                  labels={"preco_m2_usd": "US$/m²", "ano_mes": "", "produto": "Produto"})
    st.plotly_chart(fig, use_container_width=True)

    # Ratio upgrading
    st.subheader("Razão beneficiado / bruto")
    fig2 = px.area(ratio, x="ano_mes", y="ratio_upgrading",
                   labels={"ratio_upgrading": "Ratio (beneficiado/bruto)", "ano_mes": ""},
                   color_discrete_sequence=["#534AB7"])
    fig2.add_hline(y=1.0, line_dash="dash", line_color="gray", annotation_text="sem diferença")
    st.plotly_chart(fig2, use_container_width=True)

    st.info("""
    **O que monitorar:** quando o ratio cai, o Brasil está exportando mais bruto e menos valor agregado.
    A meta estratégica do setor é manter o ratio crescente — mais beneficiado, maior margem.
    """)
