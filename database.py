import sqlite3
import pandas as pd

DB_NAME = "clientes.db"


def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            inv_trafego REAL,
            inv_agencia REAL,
            vendas REAL,
            custos REAL,
            alcance INTEGER,
            interacao INTEGER,
            contatos INTEGER,
            conversao INTEGER,
            encantamento INTEGER,
            expansao INTEGER,
            defesa INTEGER,
            indicacao INTEGER
        )
    ''')
    conn.commit()
    conn.close()


def inserir_cliente(nome, trafego, agencia, vendas, custos, funil_valores):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO clientes (nome, inv_trafego, inv_agencia, vendas, custos, 
                              alcance, interacao, contatos, conversao, 
                              encantamento, expansao, defesa, indicacao)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (nome, trafego, agencia, vendas, custos, *funil_valores))
    conn.commit()
    conn.close()


def listar_clientes():
    conn = sqlite3.connect(DB_NAME)
    # Ler apenas id e nome para carregar rapidamente no Sidebar
    df = pd.read_sql_query("SELECT id, nome FROM clientes", conn)
    conn.close()
    return df


def obter_dados_cliente(cliente_id):
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query(f"SELECT * FROM clientes WHERE id = {cliente_id}", conn)
    conn.close()
    if not df.empty:
        return df.iloc[0].to_dict()
    return None
