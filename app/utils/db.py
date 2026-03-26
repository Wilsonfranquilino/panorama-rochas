import duckdb
import pandas as pd
from pathlib import Path
import streamlit as st
import os

def get_connection():
    # Caminho base do Streamlit Cloud
    raiz = Path("/mount/src/panorama-rochas")
    
    # Vamos listar TUDO o que existe na raiz para matar a dúvida dos nomes
    st.write("### 📂 Diagnóstico de Estrutura")
    arquivos_reais = []
    for root, dirs, files in os.walk(raiz):
        for name in files:
            if name.endswith(".duckdb"):
                arquivos_reais.append(os.path.join(root, name))
    
    if arquivos_reais:
        st.success(f"✅ Encontrei o banco em: `{arquivos_reais[0]}`")
        db_path = arquivos_reais[0]
    else:
        st.error("❌ Nenhum arquivo .duckdb foi encontrado no projeto!")
        st.write("Arquivos na raiz:", os.listdir(raiz))
        return None

    return duckdb.connect(db_path, read_only=True)

def query(sql: str) -> pd.DataFrame:
    con = get_connection()
    if con:
        try:
            return con.execute(sql).df()
        except Exception as e:
            st.error(f"Erro na query: {e}")
            return pd.DataFrame()
    return pd.DataFrame()