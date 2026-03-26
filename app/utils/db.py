import duckdb
import pandas as pd
from pathlib import Path
import streamlit as st

# Caminho dinâmico para a raiz do projeto
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DB_PATH = BASE_DIR / "data" / "gold" / "panorama.duckdb"

@st.cache_resource
def get_connection():
    if not DB_PATH.exists():
        st.error(f"Arquivo não encontrado em: {DB_PATH}")
        return None
    return duckdb.connect(str(DB_PATH), read_only=True)

def query(sql: str) -> pd.DataFrame:
    con = get_connection()
    if con:
        try:
            return con.execute(sql).df()
        except Exception as e:
            # RAIO-X: Se der erro, mostramos o que TEM dentro do banco
            st.error(f"Erro na consulta: {e}")
            tabelas_reais = con.execute("PRAGMA show_tables").df()
            st.write("### 🔍 Tabelas encontradas no banco:")
            st.dataframe(tabelas_reais)
            return pd.DataFrame() # Retorna vazio para não travar tudo
    return pd.DataFrame()