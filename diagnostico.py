import duckdb
import os
import pandas as pd

# Caminho do seu banco de dados
db_path = 'data/local.db'

if os.path.exists(db_path):
    con = duckdb.connect(db_path)
    
    print("\n--- TESTE DE GRANULARIDADE (TABELA GOLD) ---")
    # Este comando busca os dados reais que o seu dashboard está lendo
    query = """
        SELECT 
            ano_mes, 
            produto, 
            preco_m2_usd 
        FROM gold_preco_produto 
        WHERE volume_m2 > 0 
        ORDER BY ano_mes DESC, produto 
        LIMIT 20
    """
    df = con.execute(query).df()
    print(df)
else:
    print(f"ERRO: O arquivo {db_path} não foi encontrado na pasta data!")