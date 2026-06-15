-- Criar a tabela de produtos
CREATE TABLE IF NOT EXISTS produtos (
    id SERIAL PRIMARY KEY,
    nome TEXT NOT NULL UNIQUE,
    codigo TEXT,
    quantidade_atual REAL NOT NULL DEFAULT 0,
    unidade TEXT NOT NULL DEFAULT 'un'
);

-- Criar a tabela de entradas
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
);

-- Criar a tabela de saidas com chave estrangeira para produtos
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
);

-- Sugestão: Criar índices para melhorar a performance de busca por pedido
CREATE INDEX IF NOT EXISTS idx_entradas_pedido ON entradas(numero_pedido);
CREATE INDEX IF NOT EXISTS idx_saidas_pedido ON saidas(numero_pedido);
CREATE INDEX IF NOT EXISTS idx_produtos_nome ON produtos(nome);