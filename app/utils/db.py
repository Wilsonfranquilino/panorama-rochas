import duckdb
import pandas as pd
from pathlib import Path
import streamlit as st

# Esta linha pega a raiz do projeto "panorama-rochas" com precisão
# Ela sobe: utils -> app -> raiz
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DB_PATH = BASE_DIR / "data" / "gold" / "panorama.duckdb"

@st.cache_resource
def get_connection():
    # Isso vai nos mostrar exatamente onde o Streamlit está procurando
    if not DB_PATH.exists():
        st.error(f"🚨 Banco não encontrado!")
        st.info(f"Caminho tentado: {DB_PATH}")
        # Lista os arquivos na raiz para a gente conferir
        arquivos_raiz = [f.name for f in BASE_DIR.iterdir()]
        st.write("Arquivos na raiz do projeto:", arquivos_raiz)
        return None
    return duckdb.connect(str(DB_PATH), read_only=True)

def query(sql: str) -> pd.DataFrame:
    con = get_connection()
    if con:
        try:
            return con.execute(sql).df()
        except Exception as e:
            st.error(f"Erro na consulta: {e}")
            return pd.DataFrame()
    return pd.DataFrame()