# estoque.py - Lógica de processamento de produtos e movimentações
import psycopg2
from psycopg2 import extras
from database import get_connection

def cadastrar_produto(nome: str, quantidade_inicial: float, quantidade_minima: float = 0, unidade: str = 'un', codigo: str = None):
    """Insere um novo produto no catálogo."""
    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO produtos (nome, quantidade_atual, unidade, codigo) VALUES (%s, %s, %s, %s)",
                    (nome, quantidade_inicial, unidade, codigo)
                )
        return True
    except Exception:
        return False
    finally:
        conn.close()

def registrar_entrada_vinculada(nome_produto: str, codigo_produto: str, numero_pedido: str, nome_cliente: str, quantidade: float, fornecedor: str):
    """Registra entrada vinculada a pedido, cadastrando o produto se necessário."""
    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT id FROM produtos WHERE nome = %s", (nome_produto,))
                row = cursor.fetchone()
                
                if row:
                    produto_id = row[0]
                    cursor.execute("UPDATE produtos SET quantidade_atual = quantidade_atual + %s WHERE id = %s", (quantidade, produto_id))
                else:
                    # No Postgres, usamos RETURNING id para obter o ID gerado
                    cursor.execute(
                        "INSERT INTO produtos (nome, quantidade_atual, codigo) VALUES (%s, %s, %s) RETURNING id",
                        (nome_produto, quantidade, codigo_produto)
                    )
                    produto_id = cursor.fetchone()[0]

                cursor.execute("""
                    INSERT INTO entradas (produto_id, nome_produto, codigo_produto, numero_pedido, nome_cliente, quantidade, fornecedor) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (produto_id, nome_produto, codigo_produto, numero_pedido, nome_cliente, quantidade, fornecedor))
        return produto_id
    finally:
        conn.close()

def get_detalhes_pedido(numero_pedido: str):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT nome_cliente FROM entradas WHERE numero_pedido = %s LIMIT 1", (numero_pedido,))
            row_cliente = cursor.fetchone()
            if not row_cliente: return None, []
            
            cursor.execute("""
                SELECT DISTINCT p.id, p.nome, p.quantidade_atual, p.unidade
                FROM entradas e JOIN produtos p ON e.produto_id = p.id WHERE e.numero_pedido = %s
            """, (numero_pedido,))
            return row_cliente[0], cursor.fetchall()
    finally:
        conn.close()

def get_produto_saldo(produto_id: int) -> float:
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT quantidade_atual FROM produtos WHERE id = %s", (produto_id,))
            row = cursor.fetchone()
            return row[0] if row else 0.0
    finally:
        conn.close()

def dar_baixa_fracionada(produto_id: int, pedido: str, cliente: str, quantidade: float, manuseio: str = "", retirado_por: str = ""):
    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT nome, quantidade_atual, unidade FROM produtos WHERE id = %s", (produto_id,))
                row = cursor.fetchone()
                if not row: raise ValueError("Produto não encontrado.")
                
                nome, saldo_atual, unidade = row
                if saldo_atual < quantidade: raise ValueError(f"Estoque insuficiente.")
                    
                cursor.execute("UPDATE produtos SET quantidade_atual = quantidade_atual - %s WHERE id = %s", (quantidade, produto_id))
                cursor.execute("""
                    INSERT INTO saidas (produto_id, numero_pedido, nome_cliente, quantidade_baixada, manuseio, retirado_por) 
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (produto_id, pedido, cliente, quantidade, manuseio, retirado_por))
    finally:
        conn.close()

def get_historico_saidas():
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """SELECT s.id, p.nome, s.numero_pedido, s.nome_cliente, s.quantidade_baixada, s.manuseio, s.retirado_por, s.data_saida, p.unidade
                   FROM saidas s JOIN produtos p ON s.produto_id = p.id ORDER BY s.data_saida DESC"""
            )
            return cursor.fetchall()
    finally:
        conn.close()

def listar_saldo_estoque():
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT p.id, e.numero_pedido, e.nome_cliente, p.nome, p.codigo, p.quantidade_atual, p.unidade 
                FROM produtos p LEFT JOIN entradas e ON p.id = e.produto_id
                GROUP BY p.id, e.numero_pedido, e.nome_cliente, p.nome, p.codigo, p.quantidade_atual, p.unidade
            """)
            return cursor.fetchall()
    finally:
        conn.close()

def get_historico_entradas():
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id, nome_produto, codigo_produto, numero_pedido, nome_cliente, quantidade, fornecedor, data_entrada FROM entradas ORDER BY data_entrada DESC")
            return cursor.fetchall()
    finally:
        conn.close()

def buscar_produtos(termo: str):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT nome, codigo, quantidade_atual, unidade FROM produtos WHERE nome LIKE %s OR codigo LIKE %s", (f"%{termo}%", f"%{termo}%"))
            return cursor.fetchall()
    finally:
        conn.close()

def get_entrada_by_id(id_entrada: int):
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=extras.DictCursor) as cursor:
            cursor.execute("SELECT * FROM entradas WHERE id = %s", (id_entrada,))
            return cursor.fetchone()
    finally:
        conn.close()

def get_saida_by_id(id_saida: int):
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=extras.DictCursor) as cursor:
            cursor.execute("""
                SELECT s.*, p.nome AS produto_nome, p.codigo AS produto_codigo
                FROM saidas s JOIN produtos p ON s.produto_id = p.id WHERE s.id = %s
            """, (id_saida,))
            return cursor.fetchone()
    finally:
        conn.close()

def update_entrada(id_entrada: int, nome: str, codigo: str, pedido: str, cliente: str, qtd: float, forn: str):
    """Atualiza uma entrada e ajusta o saldo do produto proporcionalmente."""
    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT produto_id, quantidade FROM entradas WHERE id = %s", (id_entrada,))
                row = cursor.fetchone()
                if not row: return
                
                produto_id, old_qtd = row
                diff = qtd - old_qtd
                
                # Ajusta estoque: se a nova quantidade é maior, adiciona a diferença ao estoque
                cursor.execute("UPDATE produtos SET quantidade_atual = quantidade_atual + %s WHERE id = %s", (diff, produto_id))
                
                cursor.execute("""
                    UPDATE entradas SET nome_produto=%s, codigo_produto=%s, numero_pedido=%s, 
                    nome_cliente=%s, quantidade=%s, fornecedor=%s WHERE id=%s
                """, (nome, codigo, pedido, cliente, qtd, forn, id_entrada))
    finally:
        conn.close()

def update_saida(id_saida: int, pedido: str, cliente: str, qtd: float, manuseio: str, retirado: str):
    """Atualiza uma saída e ajusta o saldo do produto proporcionalmente."""
    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT produto_id, quantidade_baixada FROM saidas WHERE id = %s", (id_saida,))
                row = cursor.fetchone()
                if not row: return
                
                produto_id, old_qtd = row
                diff = qtd - old_qtd
                
                # Ajusta estoque: se a saída aumentou, o estoque deve diminuir pela diferença
                cursor.execute("UPDATE produtos SET quantidade_atual = quantidade_atual - %s WHERE id = %s", (diff, produto_id))
                
                cursor.execute("""
                    UPDATE saidas SET numero_pedido=%s, nome_cliente=%s, quantidade_baixada=%s, 
                    manuseio=%s, retirado_por=%s WHERE id=%s
                """, (pedido, cliente, qtd, manuseio, retirado, id_saida))
    finally:
        conn.close()

def excluir_entrada(id_entrada: int):
    """Exclui uma entrada e reverte o saldo do estoque."""
    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT produto_id, quantidade FROM entradas WHERE id = %s", (id_entrada,))
                row = cursor.fetchone()
                if row:
                    # Subtrai do estoque a quantidade que havia entrado
                    cursor.execute("UPDATE produtos SET quantidade_atual = quantidade_atual - %s WHERE id = %s", (row[1], row[0]))
                    cursor.execute("DELETE FROM entradas WHERE id = %s", (id_entrada,))
    finally:
        conn.close()

def excluir_saida(id_saida: int):
    """Exclui uma saída e devolve a quantidade ao estoque."""
    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT produto_id, quantidade_baixada FROM saidas WHERE id = %s", (id_saida,))
                row = cursor.fetchone()
                if row:
                    # Adiciona de volta ao estoque a quantidade que havia saído
                    cursor.execute("UPDATE produtos SET quantidade_atual = quantidade_atual + %s WHERE id = %s", (row[1], row[0]))
                    cursor.execute("DELETE FROM saidas WHERE id = %s", (id_saida,))
    finally:
        conn.close()
