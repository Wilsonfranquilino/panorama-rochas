"""Panorama das Rochas Naturais — App Principal"""
import streamlit as st
from dotenv import load_dotenv
load_dotenv()
 
st.set_page_config(
    page_title="Panorama Rochas Naturais",
    page_icon="🪨",
    layout="wide",
    initial_sidebar_state="expanded",
)
 
import home
from pages.ivm         import render as ivm
from pages.radar       import render as radar
from pages.valorizacao import render as valorizacao
from pages.comparacao  import render as comparacao
from pages.chat        import render as chat
 
PAGINAS = {
    "🏠 Visão Geral":             home,
    "📊 Comparação Ano a Ano":    comparacao,
    "⚠️ IVM — Vulnerabilidade":   ivm,
    "🌍 Radar de Oportunidades":  radar,
    "💎 Monitor de Valorização":  valorizacao,
    "🤖 Analista IA":             chat,
}
 
with st.sidebar:
    st.title("Panorama\nRochas Naturais 🪨")
    st.caption("Arquitetura Medallion · Docker · DuckDB")
    st.divider()
    pagina = st.radio("Navegação", list(PAGINAS.keys()))
    st.divider()
    st.caption("Fontes: COMEX · IBGE · BCB · ANM · Centrorochas")
    st.caption("Pipeline: Bronze → Silver → Gold")
 
PAGINAS[pagina]()
 