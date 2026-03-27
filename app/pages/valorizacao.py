"""Página Monitor de Valorização."""
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from utils.db import query

def render():
    st.title("Monitor de Valorização do Produto")
    
    # --- Guia Estratégico de Valorização (Visão de Negócio) ---
    with st.expander("💡 Diretrizes para Análise de Valorização e Upgrading", expanded=False):
        st.markdown("""
        Este monitor analisa a capacidade do setor em capturar valor e proteger margens operacionais no mercado internacional.
        
        * **Evolução do Preço Médio (US$/m²):** Indica o posicionamento de mercado. Tendências de alta refletem maior valor agregado ou demanda em segmentos de alto padrão.
        * **Mix de Exportação:** Monitora a transição entre rochas **Brutas vs. Beneficiadas**. O objetivo estratégico é a expansão do volume beneficiado (Azul Escuro).
        * **Ratio de Upgrading:** Mede o multiplicador de valor gerado pelo processo de industrialização. 
            * *Ratio > 1.0:* O beneficiamento está agregando valor econômico real ao produto bruto.
        * **Performance YoY (Year-over-Year):** Compara o desempenho do preço médio anual contra o ciclo anterior para identificar a maturidade dos preços.
        """)

    # --- Coleta de Dados ---
    val   = query("SELECT * FROM metric_valorizacao ORDER BY ano_mes")
    ratio = query("SELECT * FROM metric_upgrading_ratio ORDER BY ano_mes")

    if val.empty:
        st.warning("Dados de valorização não disponíveis no momento.")
        return

    # --- Filtros Unificados (Ação Global na Página) ---
    col1, col2 = st.columns(2)
    produtos   = val["produto"].dropna().unique().tolist()
    categorias = val["categoria"].dropna().unique().tolist()
    
    # O que for selecionado aqui, altera todos os gráficos abaixo automaticamente
    selecionados = col1.multiselect("Filtrar Materiais", produtos, default=produtos)
    cats_sel     = col2.multiselect("Filtrar Categorias", categorias, default=categorias)

    # DataFrame principal filtrado que alimenta a página
    filtrado = val[
        val["produto"].isin(selecionados) &
        val["categoria"].isin(cats_sel)
    ]

    # --- Painel de Indicadores (KPIs) ---
    if not filtrado.empty:
        ultimo_mes   = filtrado["ano_mes"].max()
        primeiro_mes = filtrado["ano_mes"].min()
        
        # Média ponderada apenas para o KPI de topo
        preco_atual  = filtrado[filtrado["ano_mes"] == ultimo_mes]["preco_m2_usd"].mean()
        preco_inicial= filtrado[filtrado["ano_mes"] == primeiro_mes]["preco_m2_usd"].mean()
        variacao     = ((preco_atual - preco_inicial) / preco_inicial * 100) if preco_inicial else 0

        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Preço Médio (Atual)", f"US$ {preco_atual:.2f}/m²")
        k2.metric("Preço Médio (Inicial)", f"US$ {preco_inicial:.2f}/m²")
        k3.metric("Valorização Acumulada", f"{variacao:+.1f}%")
        
        if not ratio.empty:
            r = ratio[ratio["ano_mes"] == ratio["ano_mes"].max()]["ratio_upgrading"].values
            k4.metric("Ratio Upgrading", f"{r[0]:.2f}x" if len(r) else "—")

    st.divider()

    # --- Gráfico 1: Evolução Histórica de Preços ---
    st.subheader("Tendência de Preços Médios (Série Histórica)")
    fig = px.line(filtrado, x="ano_mes", y="preco_m2_usd", color="produto",
                  labels={"preco_m2_usd":"US$/m²","ano_mes":"Período","produto":"Material"},
                  color_discrete_sequence=px.colors.qualitative.Prism)
    fig.update_layout(xaxis_tickangle=-45, legend=dict(orientation="h", y=-0.25))
    st.plotly_chart(fig, use_container_width=True)

    col_a, col_b = st.columns(2)

    # --- Gráfico 2: Volume por Grau de Elaboração ---
    with col_a:
        st.subheader("Volume por Categoria")
        vol_df = filtrado.groupby(["ano_mes","categoria"])["volume_m2"].sum().reset_index()
        fig2 = px.area(vol_df, x="ano_mes", y="volume_m2", color="categoria",
                       labels={"volume_m2":"Volume (m²)","ano_mes":"","categoria":"Tipo"},
                       color_discrete_map={"Bruto":"#85B7EB","Beneficiado":"#185FA5"})
        fig2.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig2, use_container_width=True)

    # --- Gráfico 3: Ratio de Industrialização ---
    with col_b:
        st.subheader("Agregação de Valor (Ratio)")
        if not ratio.empty:
            fig3 = go.Figure()
            fig3.add_trace(go.Scatter(
                x=ratio["ano_mes"], y=ratio["ratio_upgrading"],
                fill="tozeroy", mode="lines",
                line=dict(color="#534AB7"),
                fillcolor="rgba(83,74,183,0.15)"
            ))
            fig3.add_hline(y=1.0, line_dash="dash", line_color="gray",
                           annotation_text="Paridade Bruto/Beneficiado")
            fig3.update_layout(xaxis_tickangle=-45, yaxis_title="Multiplicador", xaxis_title="")
            st.plotly_chart(fig3, use_container_width=True)

    # --- SEÇÃO FINAL: VALORIZAÇÃO ANUAL (YOY %) ---
    st.divider()
    st.subheader("📊 Análise de Performance: Valorização Anual (YoY %)")
    
    st.markdown("""
    Este indicador compara o preço médio anual consolidado contra o ano anterior, permitindo visualizar a **sustentabilidade do crescimento**.
    """)
    
    if not filtrado.empty:
        yoy_df = filtrado.copy()
        yoy_df['ano'] = yoy_df['ano_mes'].astype(str).str.slice(0, 4)
        
        # CORREÇÃO CRÍTICA: Ordenamos por data e pegamos o último registro de cada ano por produto
        # Isso garante que a barra mostre a valorização real de cada material sem diluir em médias.
        yoy_anual = yoy_df.sort_values('ano_mes').groupby(['ano', 'produto']).last().reset_index()

        fig4 = px.bar(
            yoy_anual, 
            x="ano", 
            y="variacao_yoy_pct",
            color="produto",
            barmode="group",
            text_auto='.1f',
            title="Variação Percentual de Valor (Ano sobre Ano)",
            labels={"variacao_yoy_pct": "Variação (%)", "ano": "Ano Fiscal", "produto": "Material"},
            color_discrete_sequence=px.colors.qualitative.Prism
        )
        
        fig4.add_hline(y=0, line_dash="dash", line_color="white")
        fig4.update_layout(
            xaxis_type='category', 
            legend=dict(orientation="h", y=-0.3),
            margin=dict(t=50)
        )
        
        st.plotly_chart(fig4, use_container_width=True)
        
        st.info("""
        **Nota Analítica:** Taxas de crescimento positivas confirmam a resiliência do preço médio no mercado. 
        Uma desaceleração na taxa (barras menores) indica estabilização de preço após períodos de forte demanda.
        """)
    else:
        st.warning("⚠️ Selecione ao menos um material no filtro superior para habilitar a análise YoY.")