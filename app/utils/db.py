"""Utilitário de conexão com DuckDB Gold."""
import os
import duckdb
import pandas as pd
from pathlib import Path
import streamlit as st

GOLD_PATH = Path(os.getenv("GOLD_PATH", "/data/gold"))

@st.cache_resource
def get_connection():
    db = GOLD_PATH / "panorama.duckdb"
    return duckdb.connect(str(db), read_only=True)

def query(sql: str) -> pd.DataFrame:
    con = get_connection()
    return con.execute(sql).df()
