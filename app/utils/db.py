import duckdb
import pandas as pd
from pathlib import Path
import streamlit as st

def get_connection():
    # Caminho absoluto da raiz no Streamlit Cloud
    # utils -> app -> raiz
    raiz = Path(__file__).resolve().parent.parent.parent
    
    # Use o nome EXATO que aparece no VS Code (provavelmente 'data')
    db_path = raiz / "data" / "gold" / "panorama.duckdb"

    if not db_path.exists():
        st.error(f"🚨 Arquivo não encontrado!")
        st.write(f"O Python tentou ler: `{db_path}`")
        # Listagem para você ver o nome real da pasta sem tradução
        st.write("Conteúdo real da raiz:", [f.name for f in raiz.iterdir()])
        return None

    return duckdb.connect(str(db_path), read_only=True)

def query(sql: str) -> pd.DataFrame:
    con = get_connection()
    if con:
        try:
            return con.execute(sql).df()
        except Exception as e:
            st.error(f"Erro na query: {e}")
            return pd.DataFrame()
    return pd.DataFrame()