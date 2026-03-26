import duckdb
import pandas as pd
from pathlib import Path
import streamlit as st

def get_connection():
    # Caminho direto que já confirmamos no diagnóstico anterior
    db_path = "/mount/src/panorama-rochas/data/gold/panorama.duckdb"
    
    try:
        # Tenta conectar. Se o arquivo não existir, o DuckDB cria um novo (o que evitaria erro, mas queremos ler apenas)
        return duckdb.connect(db_path, read_only=True)
    except Exception as e:
        st.error(f"❌ Erro ao conectar ao banco de dados: {e}")
        return None

def query(sql: str) -> pd.DataFrame:
    con = get_connection()
    if con:
        try:
            df = con.execute(sql).df()
            con.close() # Importante fechar a conexão após a query
            return df
        except Exception as e:
            st.error(f"Erro na execução da query: {e}")
            return pd.DataFrame()
    return pd.DataFrame()