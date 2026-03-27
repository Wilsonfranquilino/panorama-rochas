"""Página Home — visão geral com filtros."""
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from utils.db import query
 
def render():
    st.title("Panorama das Rochas Naturais — Brasil")
    # --- Guia Estratégico de Comparação ---
    with st.expander("💡 Como interpretar esta Comparação para decisão", expanded=False):
        st.markdown("""
        Esta página permite analisar a evolução real do setor comparando dois períodos distintos.
        
        * **FOB Base vs. Comparação:** Identifique se o faturamento total cresceu ou retraiu em termos nominais.
        * **Comparação por Granularidade:** Use para ver quais mercados (países) ou produtos (rochas) ganharam ou perderam relevância física no gráfico de barras.
        * **Variação Percentual:** As barras **verdes** indicam expansão e novos mercados. As barras **laranjas** mostram onde o setor está perdendo fôlego.
        * **Tabela de Auditoria:** Use para extrair os valores exatos em milhões de dólares para relatórios técnicos.
        """)
    st.caption("Dados: COMEX Stat · IBGE · BCB · ANM · Centrorochas")
 
    # --- Filtros globais ---
    with st.expander("Filtros", expanded=True):
        col1, col2, col3 = st.columns(3)
        anos_disp   = query("SELECT DISTINCT ano FROM gold_exportacoes ORDER BY ano")["ano"].tolist()
        paises_disp = query("SELECT DISTINCT pais_nome FROM gold_exportacoes ORDER BY pais_nome")["pais_nome"].tolist()
        ncms_disp   = query("SELECT DISTINCT ncm_desc FROM gold_exportacoes ORDER BY ncm_desc")["ncm_desc"].tolist()
 
        anos_sel   = col1.multiselect("Ano", anos_disp, default=anos_disp[-3:])
        paises_sel = col2.multiselect("País", paises_disp, default=paises_disp[:5])
        ncms_sel   = col3.multiselect("Tipo de rocha", ncms_disp, default=ncms_disp)
 
    if not anos_sel:   anos_sel   = anos_disp
    if not paises_sel: paises_sel = paises_disp
    if not ncms_sel:   ncms_sel   = ncms_disp
 
    anos_str   = ",".join(str(a) for a in anos_sel)
    paises_str = "','".join(paises_sel)
    ncms_str   = "','".join(ncms_sel)
 
    df = query(f"""
        SELECT * FROM gold_exportacoes
        WHERE ano IN ({anos_str})
          AND pais_nome IN ('{paises_str}')
          AND ncm_desc  IN ('{ncms_str}')
    """)
 
    if df.empty:
        st.warning("Nenhum dado para os filtros selecionados.")
        return
 
    # --- KPIs ---
    st.divider()
    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("FOB Total",        f"US$ {df['fob_usd'].sum()/1e9:.2f}bi")
    k2.metric("Países",           df['pais_nome'].nunique())
    k3.metric("Tipos de rocha",   df['ncm_desc'].nunique())
    k4.metric("Estados",          df['estado'].nunique())
    k5.metric("Registros",        f"{len(df):,}")
 
    st.divider()
 
    # --- Gráfico 1: Evolução mensal FOB ---
    st.subheader("Exportações por mês")
    mensal = df.groupby(["ano","mes"])["fob_usd"].sum().reset_index()
    mensal["periodo"] = mensal["ano"].astype(str) + "-" + mensal["mes"].astype(str).str.zfill(2)
    fig1 = px.line(mensal, x="periodo", y="fob_usd",
                   labels={"fob_usd":"FOB (US$)","periodo":""},
                   color_discrete_sequence=["#185FA5"])
    fig1.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig1, use_container_width=True)
 
    col_a, col_b = st.columns(2)
 
    # --- Gráfico 2: Top países ---
    with col_a:
        st.subheader("Top países")
        top_paises = (df.groupby("pais_nome")["fob_usd"].sum()
                        .reset_index()
                        .sort_values("fob_usd", ascending=True)
                        .tail(10))
        fig2 = px.bar(top_paises, x="fob_usd", y="pais_nome", orientation="h",
                      labels={"fob_usd":"FOB (US$)","pais_nome":""},
                      color="fob_usd", color_continuous_scale="Blues")
        fig2.update_layout(coloraxis_showscale=False)
        st.plotly_chart(fig2, use_container_width=True)
 
    # --- Gráfico 3: Mix de produtos ---
    with col_b:
        st.subheader("Mix de produtos")
        mix = df.groupby("ncm_desc")["fob_usd"].sum().reset_index()
        fig3 = px.pie(mix, values="fob_usd", names="ncm_desc",
                      color_discrete_sequence=px.colors.qualitative.Set2,
                      hole=0.4)
        fig3.update_traces(textposition="inside", textinfo="percent+label")
        st.plotly_chart(fig3, use_container_width=True)
 
    # --- Gráfico 4: Exportações por estado ---
    st.subheader("Participação por estado exportador")
    estados = (df.groupby("estado")["fob_usd"].sum()
                 .reset_index()
                 .sort_values("fob_usd", ascending=False))
    fig4 = px.bar(estados, x="estado", y="fob_usd",
                  labels={"fob_usd":"FOB (US$)","estado":"Estado"},
                  color="fob_usd", color_continuous_scale="Teal")
    fig4.update_layout(coloraxis_showscale=False)
    st.plotly_chart(fig4, use_container_width=True)
 
    # --- Gráfico 5: Heatmap mês × país ---
    st.subheader("Heatmap — exportações por mês e país (top 8)")
    top8 = df.groupby("pais_nome")["fob_usd"].sum().nlargest(8).index.tolist()
    heat = (df[df["pais_nome"].isin(top8)]
              .groupby(["mes","pais_nome"])["fob_usd"].sum()
              .reset_index())
    heat_pivot = heat.pivot(index="pais_nome", columns="mes", values="fob_usd").fillna(0)
    fig5 = px.imshow(heat_pivot, aspect="auto",
                     labels={"x":"Mês","y":"País","color":"FOB (US$)"},
                     color_continuous_scale="Blues")
    st.plotly_chart(fig5, use_container_width=True)