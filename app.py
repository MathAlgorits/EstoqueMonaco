# app.py - Ponto de entrada do sistema
from database import init_db
import estoque

def menu_teste():
    # Inicializa as tabelas
    init_db()
    
    print("--- Teste de Operação: Dropshipping & Fracionamento ---")
    
    # 1. Cadastro Inicial
    estoque.cadastrar_produto("Polímero Base A", 10.0, quantidade_minima=5.0, unidade="kg") 
    estoque.cadastrar_produto("Solvente B", 5.0, quantidade_minima=2.0, unidade="L")
    
    # 2. Entrada de Estoque
    estoque.dar_entrada(1, 5.5) # Adicionando mais 5.5 unidades
    print("\n--- SALDO ATUAL EM ESTOQUE ---")
    for item in estoque.listar_saldo_estoque():
        print(f"ID: {item[0]} | Produto: {item[1]} | Saldo: {item[2]:.3f} {item[3]}")

    # 3. Baixa de Pedido
    try:
        estoque.dar_baixa_fracionada(1, "PED-99", "Marcos Oliveira", 2.350)
        print("Baixa fracionada de 2.350 unidades realizada.")
    except ValueError as e:
        print(f"Erro na baixa: {e}")

    print("\n--- HISTÓRICO DE SAÍDAS ---")
    for s in estoque.get_historico_saidas():
        print(f"Pedido: {s[2]} | Cliente: {s[3]} | Qtd: {s[4]:.3f} {s[6]} | Data: {s[5]}")

    print("\n--- ALERTAS DE ESTOQUE BAIXO ---")
    alertas = estoque.listar_estoque_baixo()
    if not alertas:
        print("Tudo em dia! Todos os itens acima do nível mínimo.")
    for a in alertas:
        print(f"ALERTA: {a[1]} está com {a[2]:.3f} {a[4]} (Mínimo: {a[3]:.3f} {a[4]})")

if __name__ == "__main__":
    menu_teste()
