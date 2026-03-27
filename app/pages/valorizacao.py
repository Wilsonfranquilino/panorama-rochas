"""Página Monitor de Valorização."""
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from utils.db import query
 
def render():
    st.title("Monitor de Valorização do Produto")
    # --- Guia Estratégico de Valorização (Padrão Home) ---
    with st.expander("💡 Como interpretar a Valorização e o Upgrading", expanded=False):
        st.markdown("""
        Esta página monitora se o setor está conseguindo vender rochas por um preço melhor ou se está perdendo margem.
        
        * **Preço Médio (US$/m²):** Acompanhe a linha de tendência por produto. Subidas indicam maior aceitação no mercado de luxo ou escassez de materiais específicos.
        * **Volume por Categoria:** Compara o volume de rochas **Brutas vs. Beneficiadas**. O objetivo é ver a cor azul escura (Beneficiado) crescer sobre a clara.
        * **Ratio Upgrading:** É o indicador de "pulo do gato". Ele mostra quantas vezes o produto beneficiado é mais caro que o bruto. 
            * *Ratio alto:* O beneficiamento está agregando muito valor.
            * *Ratio baixo:* O custo de processar não está sendo repassado ao preço final.
        * **Variação YoY (Year-over-Year):** Compara o preço do mês atual com o mesmo mês do ano anterior, eliminando distorções sazonais.
        """)
 
    val   = query("SELECT * FROM metric_valorizacao ORDER BY ano_mes")
    ratio = query("SELECT * FROM metric_upgrading_ratio ORDER BY ano_mes")
 
    if val.empty:
        st.warning("Dados de valorização não disponíveis.")
        return
 
    # Filtros
    col1, col2 = st.columns(2)
    produtos   = val["produto"].dropna().unique().tolist()
    categorias = val["categoria"].dropna().unique().tolist()
    selecionados = col1.multiselect("Produtos",   produtos,   default=produtos)
    cats_sel     = col2.multiselect("Categoria",  categorias, default=categorias)
 
    filtrado = val[
        val["produto"].isin(selecionados) &
        val["categoria"].isin(cats_sel)
    ]
 
    # KPIs
    ultimo_mes   = filtrado["ano_mes"].max()
    primeiro_mes = filtrado["ano_mes"].min()
    preco_atual  = filtrado[filtrado["ano_mes"] == ultimo_mes]["preco_m2_usd"].mean()
    preco_inicial= filtrado[filtrado["ano_mes"] == primeiro_mes]["preco_m2_usd"].mean()
    variacao     = ((preco_atual - preco_inicial) / preco_inicial * 100) if preco_inicial else 0
 
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Preço médio atual",     f"US$ {preco_atual:.2f}/m²")
    k2.metric("Preço inicial (série)", f"US$ {preco_inicial:.2f}/m²")
    k3.metric("Valorização total",     f"{variacao:+.1f}%")
    if not ratio.empty:
        r = ratio[ratio["ano_mes"] == ratio["ano_mes"].max()]["ratio_upgrading"].values
        k4.metric("Ratio upgrading atual", f"{r[0]:.2f}x" if len(r) else "—")
 
    st.divider()
 
    # Preço por produto
    st.subheader("Evolução do preço médio por m²")
    fig = px.line(filtrado, x="ano_mes", y="preco_m2_usd", color="produto",
                  labels={"preco_m2_usd":"US$/m²","ano_mes":"","produto":"Produto"},
                  color_discrete_sequence=px.colors.qualitative.Set2)
    fig.update_layout(xaxis_tickangle=-45, legend=dict(orientation="h", y=-0.25))
    st.plotly_chart(fig, use_container_width=True)
 
    col_a, col_b = st.columns(2)
 
    # Volume por categoria
    with col_a:
        st.subheader("Volume exportado (m²)")
        vol = filtrado.groupby(["ano_mes","categoria"])["volume_m2"].sum().reset_index()
        fig2 = px.area(vol, x="ano_mes", y="volume_m2", color="categoria",
                       labels={"volume_m2":"Volume (m²)","ano_mes":"","categoria":"Categoria"},
                       color_discrete_map={"Bruto":"#85B7EB","Beneficiado":"#185FA5"})
        fig2.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig2, use_container_width=True)
 
    # Ratio upgrading
    with col_b:
        st.subheader("Ratio upgrading — beneficiado/bruto")
        if not ratio.empty:
            fig3 = go.Figure()
            fig3.add_trace(go.Scatter(
                x=ratio["ano_mes"], y=ratio["ratio_upgrading"],
                fill="tozeroy", mode="lines",
                line=dict(color="#534AB7"),
                fillcolor="rgba(83,74,183,0.15)"
            ))
            fig3.add_hline(y=1.0, line_dash="dash", line_color="gray",
                           annotation_text="sem diferença de valor")
            fig3.update_layout(xaxis_tickangle=-45, yaxis_title="Ratio", xaxis_title="")
            st.plotly_chart(fig3, use_container_width=True)
 
    # Variação YoY
    st.subheader("Variação anual do preço (YoY)")
    yoy = filtrado[filtrado["variacao_yoy_pct"].notna()].copy()
    if not yoy.empty:
        fig4 = px.bar(yoy, x="ano_mes", y="variacao_yoy_pct", color="produto",
                      barmode="group",
                      labels={"variacao_yoy_pct":"Var YoY (%)","ano_mes":"","produto":"Produto"},
                      color_discrete_sequence=px.colors.qualitative.Set2)
        fig4.add_hline(y=0, line_dash="dash", line_color="gray")
        fig4.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig4, use_container_width=True)
 
    st.info("""
    **Estratégia de upgrading:** quando o ratio cai, o Brasil exporta mais bruto — menor margem.
    Meta: manter ratio crescente — mais beneficiado, maior receita por m².
    """)