import psycopg2

def get_connection():
    # Passamos os teus dados reais diretamente, sem depender de travas do secrets do Streamlit
    return psycopg2.connect(
        host="aws-1-sa-east-1.pooler.supabase.com",
        database="postgres",
        user="postgres.rjocfajczvevbfyoupjw",
        password="Monacodb2026!",
        port=5432,
        sslmode="require"
    )

def init_db():
    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cursor:
                # Postgres usa SERIAL para autoincremento
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS produtos (
                        id SERIAL PRIMARY KEY,
                        nome TEXT NOT NULL UNIQUE,
                        codigo TEXT,
                        quantidade_atual REAL NOT NULL DEFAULT 0,
                        unidade TEXT NOT NULL DEFAULT 'un'
                    )
                """)
                
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS entradas (
                        id SERIAL PRIMARY KEY,
                        produto_id INTEGER,
                        nome_produto TEXT NOT NULL,
                        codigo_produto TEXT,
                        numero_pedido TEXT NOT NULL,
                        nome_cliente TEXT NOT NULL,
                        quantidade REAL NOT NULL,
                        fornecedor TEXT NOT NULL,
                        data_entrada TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS saidas (
                        id SERIAL PRIMARY KEY,
                        produto_id INTEGER NOT NULL,
                        numero_pedido TEXT NOT NULL,
                        nome_cliente TEXT NOT NULL,
                        quantidade_baixada REAL NOT NULL,
                        manuseio TEXT,
                        retirado_por TEXT,
                        data_saida TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (produto_id) REFERENCES produtos (id)
                    )
                """)
                conn.commit()
    finally:
        conn.close()