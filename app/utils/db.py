"""Utilitário de conexão com DuckDB Gold."""
import os
import duckdb
import pandas as pd
from pathlib import Path
import streamlit as st

# Pega o caminho de onde o db.py está e sobe os níveis necessários
# db.py está em app/utils/, então subimos 2 níveis para chegar na raiz do projeto
BASE_DIR = Path(__file__).resolve().parent.parent.parent
GOLD_PATH = BASE_DIR / "data" / "gold"

@st.cache_resource
def get_connection():
    db = GOLD_PATH / "panorama.duckdb"
    return duckdb.connect(str(db), read_only=True)

def query(sql: str) -> pd.DataFrame:
    con = get_connection()
    return con.execute(sql).df()
