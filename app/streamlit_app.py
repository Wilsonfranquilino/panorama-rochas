"""
Panorama das Rochas Naturais — App Principal
"""
import streamlit as st
from dotenv import load_dotenv
load_dotenv()

st.set_page_config(
    page_title="Panorama Rochas Naturais",
    page_icon="🪨",
    layout="wide",
    initial_sidebar_state="expanded",
)

from pages.home        import render as home
from pages.ivm         import render as ivm
from pages.radar       import render as radar
from pages.valorizacao import render as valorizacao
from pages.chat        import render as chat

PAGINAS = {
    "Visão Geral":            home,
    "IVM — Vulnerabilidade":  ivm,
    "Radar de Oportunidades": radar,
    "Monitor de Valorização": valorizacao,
    "Analista IA":            chat,
}

with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/0/05/Flag_of_Brazil.svg/320px-Flag_of_Brazil.svg.png", width=80)
    st.title("Panorama\nRochas Naturais")
    st.caption("POC — Arquitetura Medallion")
    st.divider()
    pagina = st.radio("Navegação", list(PAGINAS.keys()))
    st.divider()
    st.caption("Fontes: COMEX · IBGE · BCB · ANM · Centrorochas")

PAGINAS[pagina]()
