"""Página Comparação Ano a Ano."""
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from utils.db import query
 
def render():
    st.title("Comparação Ano a Ano")
    st.caption("Compare períodos, países e produtos lado a lado")
 
    col1, col2, col3 = st.columns(3)
    anos = query("SELECT DISTINCT ano FROM gold_exportacoes ORDER BY ano")["ano"].tolist()
    ano_a        = col1.selectbox("Ano base",       anos, index=len(anos)-2)
    ano_b        = col2.selectbox("Ano comparação", anos, index=len(anos)-1)
    granularidade = col3.selectbox("Agrupar por", ["País","Tipo de rocha","Estado","Mês"])
 
    grupo_map = {"País":"pais_nome","Tipo de rocha":"ncm_desc","Estado":"estado","Mês":"mes"}
    grupo = grupo_map[granularidade]
 
    df_a = query(f"SELECT {grupo} as dim, SUM(fob_usd) as fob FROM gold_exportacoes WHERE ano={ano_a} GROUP BY 1")
    df_b = query(f"SELECT {grupo} as dim, SUM(fob_usd) as fob FROM gold_exportacoes WHERE ano={ano_b} GROUP BY 1")
    df_a.columns = ["dim", f"fob_{ano_a}"]
    df_b.columns = ["dim", f"fob_{ano_b}"]
 
    merged = df_a.merge(df_b, on="dim", how="outer").fillna(0)
    merged["variacao_pct"] = ((merged[f"fob_{ano_b}"] - merged[f"fob_{ano_a}"]) /
                               merged[f"fob_{ano_a}"].replace(0,1) * 100).round(1)
    merged["variacao_abs"] = merged[f"fob_{ano_b}"] - merged[f"fob_{ano_a}"]
    merged = merged.sort_values(f"fob_{ano_b}", ascending=False)
 
    # KPIs
    total_a  = merged[f"fob_{ano_a}"].sum()
    total_b  = merged[f"fob_{ano_b}"].sum()
    var_total = ((total_b - total_a) / total_a * 100) if total_a > 0 else 0
 
    k1, k2, k3 = st.columns(3)
    k1.metric(f"Total {ano_a}", f"US$ {total_a/1e9:.2f}bi")
    k2.metric(f"Total {ano_b}", f"US$ {total_b/1e9:.2f}bi", f"{var_total:+.1f}%")
    k3.metric("Variação absoluta", f"US$ {(total_b-total_a)/1e6:.0f}M")
 
    st.divider()
 
    # Barras agrupadas
    st.subheader(f"Comparação por {granularidade}")
    top10 = merged.head(10)
    fig = go.Figure()
    fig.add_trace(go.Bar(name=str(ano_a), x=top10["dim"], y=top10[f"fob_{ano_a}"],
                         marker_color="#85B7EB"))
    fig.add_trace(go.Bar(name=str(ano_b), x=top10["dim"], y=top10[f"fob_{ano_b}"],
                         marker_color="#185FA5"))
    fig.update_layout(barmode="group", xaxis_tickangle=-30,
                      yaxis_title="FOB (US$)", legend_title="Ano")
    st.plotly_chart(fig, use_container_width=True)
 
    # Variação %
    st.subheader("Variação percentual")
    var_df = merged.sort_values("variacao_pct", ascending=True).head(15)
    cores  = ["#D85A30" if v < 0 else "#1D9E75" for v in var_df["variacao_pct"]]
    fig2 = go.Figure(go.Bar(
        x=var_df["variacao_pct"], y=var_df["dim"], orientation="h",
        marker_color=cores,
        text=var_df["variacao_pct"].apply(lambda x: f"{x:+.1f}%"),
        textposition="outside"
    ))
    fig2.add_vline(x=0, line_dash="dash", line_color="gray")
    fig2.update_layout(xaxis_title="Variação %", yaxis_title="")
    st.plotly_chart(fig2, use_container_width=True)
 
    # Tabela
    st.subheader("Tabela completa")
    fmt = merged.copy()
    fmt[f"fob_{ano_a}"]   = fmt[f"fob_{ano_a}"].apply(lambda x: f"US$ {x/1e6:.1f}M")
    fmt[f"fob_{ano_b}"]   = fmt[f"fob_{ano_b}"].apply(lambda x: f"US$ {x/1e6:.1f}M")
    fmt["variacao_pct"]   = fmt["variacao_pct"].apply(lambda x: f"{x:+.1f}%")
    fmt["variacao_abs"]   = fmt["variacao_abs"].apply(lambda x: f"US$ {x/1e6:+.1f}M")
    fmt.columns = [granularidade, f"FOB {ano_a}", f"FOB {ano_b}", "Var %", "Var Absoluta"]
    st.dataframe(fmt, use_container_width=True, hide_index=True)
 