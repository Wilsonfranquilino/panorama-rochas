import duckdb
import pandas as pd
from pathlib import Path
import streamlit as st

# BASE_DIR: /mount/src/panorama-rochas
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# AJUSTE AQUI: Use os nomes EXATOS das pastas que aparecem no seu GitHub
DB_PATH = BASE_DIR / "dados" / "ouro" / "panorama.duckdb"

@st.cache_resource
def get_connection():
    if not DB_PATH.exists():
        # Se não achar, vamos listar as pastas para ter certeza do nome
        st.error("🚨 Banco de dados não encontrado!")
        st.write(f"Caminho tentado: `{DB_PATH}`")
        
        # Diagnóstico de pastas
        pastas_na_raiz = [f.name for f in BASE_DIR.iterdir() if f.is_dir()]
        st.write("Pastas que o Python está vendo na raiz:", pastas_na_raiz)
        return None
        
    return duckdb.connect(str(DB_PATH), read_only=True)

def query(sql: str) -> pd.DataFrame:
    con = get_connection()
    if con is None:
        return pd.DataFrame()
    try:
        return con.execute(sql).df()
    except Exception as e:
        st.error(f"Erro na query: {e}")
        return pd.DataFrame()