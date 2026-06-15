import streamlit as st
import estoque
from database import init_db
import pandas as pd

# Inicializa st.session_state para os campos do formulário se ainda não existirem
# Isso garante que os campos possam ser limpos após o envio
if "entrada_ped_venda" not in st.session_state:
    st.session_state["entrada_ped_venda"] = ""
    st.session_state["entrada_prod_codigo"] = ""
    st.session_state["entrada_prod_nome"] = ""
    st.session_state["entrada_cliente_venda"] = ""
    st.session_state["entrada_fornecedor"] = ""
    st.session_state["entrada_qtd_ent"] = 0
    st.session_state["saida_num_pedido"] = ""
    st.session_state["saida_manuseio"] = ""
    st.session_state["saida_retirado_por"] = ""
    st.session_state["saida_produto_sel"] = "" # Adicionado para limpar o selectbox
    st.session_state["saida_qtd_saida"] = 0
    st.session_state["msg_sucesso"] = None

    # Novas variáveis de estado para o gerenciamento unificado
    st.session_state["gerenciar_id"] = ""
    st.session_state["gerenciar_tipo"] = "Entrada" # Default selection
    st.session_state["show_edit_form"] = False
    st.session_state["editing_record_data"] = None
    st.session_state["editing_record_type"] = None
    st.session_state["confirm_delete_id"] = None
    st.session_state["confirm_delete_type"] = None

# --- FUNÇÕES DE CALLBACK (Lógica de processamento e limpeza) ---

def registrar_entrada_callback():
    # Coleta dados do state (vinculados via 'key')
    ped = st.session_state.entrada_ped_venda
    cod = st.session_state.entrada_prod_codigo
    nome = st.session_state.entrada_prod_nome
    cli = st.session_state.entrada_cliente_venda
    forn = st.session_state.entrada_fornecedor
    qtd = st.session_state.entrada_qtd_ent

    if nome and ped and cli:
        estoque.registrar_entrada_vinculada(nome, cod, ped, cli, qtd, forn)
        st.session_state.msg_sucesso = f"Entrada de '{nome}' registrada com sucesso! 📥"
        
        # Limpa os campos no session_state com segurança
        st.session_state.entrada_ped_venda = ""
        st.session_state.entrada_prod_codigo = ""
        st.session_state.entrada_prod_nome = ""
        st.session_state.entrada_cliente_venda = ""
        st.session_state.entrada_fornecedor = ""
        st.session_state.entrada_qtd_ent = 0
    else:
        st.error("⚠️ Por favor, preencha todos os campos obrigatórios (Pedido, Produto e Cliente).")

def dar_baixa_callback(dict_saida, cliente_auto):
    pedido = st.session_state.saida_num_pedido
    prod_label = st.session_state.saida_produto_sel
    manuseio = st.session_state.saida_manuseio
    retirado = st.session_state.saida_retirado_por
    qtd = st.session_state.saida_qtd_saida

    if not prod_label: # Verifica se um produto foi selecionado
        st.error("⚠️ Por favor, selecione um produto para baixa.")
        return

    if qtd <= 0:
        st.error("⚠️ A quantidade de saída deve ser maior que zero.")
        return

    # Obtém o ID do produto a partir do label selecionado
    produto_id = dict_saida[prod_label]
    
    # Busca o saldo atual do produto no banco de dados
    saldo_atual = estoque.get_produto_saldo(produto_id)

    if qtd > saldo_atual:
        st.error(f"⚠️ Estoque insuficiente! Saldo atual para '{prod_label.split(' (Saldo:')[0]}': {saldo_atual} unidades.")
        return

    if prod_label in dict_saida:
        try:
            estoque.dar_baixa_fracionada(dict_saida[prod_label], pedido, cliente_auto, qtd, manuseio, retirado)
            st.session_state.msg_sucesso = f"Saída de {qtd} unidades registrada! 📤"
            
            # Limpa os campos
            st.session_state.saida_num_pedido = ""
            st.session_state.saida_manuseio = ""
            st.session_state.saida_retirado_por = ""
            st.session_state.saida_produto_sel = "" # Limpa o selectbox
            st.session_state.saida_qtd_saida = 0
        except ValueError as e:
            st.error(f"Erro: {e}")

def carregar_para_edicao_callback():
    mov_id = st.session_state.gerenciar_id
    mov_tipo = st.session_state.gerenciar_tipo
    
    if not mov_id:
        st.error("Por favor, insira o ID da movimentação.")
        return

    try:
        mov_id = int(mov_id)
        if mov_tipo == "Entrada":
            record = estoque.get_entrada_by_id(mov_id)
            if record:
                st.session_state.editing_record_data = dict(record) # Converte Row para dicionário
                st.session_state.editing_record_type = "Entrada"
                st.session_state.show_edit_form = True
                st.session_state.msg_sucesso = f"Entrada ID {mov_id} carregada para edição."
            else:
                st.error(f"Entrada com ID {mov_id} não encontrada.")
        elif mov_tipo == "Saída":
            record = estoque.get_saida_by_id(mov_id)
            if record:
                st.session_state.editing_record_data = dict(record)
                st.session_state.editing_record_type = "Saída"
                st.session_state.show_edit_form = True
                st.session_state.msg_sucesso = f"Saída ID {mov_id} carregada para edição."
            else:
                st.error(f"Saída com ID {mov_id} não encontrada.")
    except ValueError:
        st.error("O ID da movimentação deve ser um número inteiro.")
    except Exception as e:
        st.error(f"Ocorreu um erro ao carregar a movimentação: {e}")

def iniciar_exclusao_callback():
    mov_id = st.session_state.gerenciar_id
    mov_tipo = st.session_state.gerenciar_tipo

    if not mov_id:
        st.error("Por favor, insira o ID da movimentação para exclusão.")
        return
    
    try:
        mov_id = int(mov_id)
        # Define o estado de confirmação para exibir os botões de confirmação
        st.session_state.confirm_delete_id = mov_id
        st.session_state.confirm_delete_type = mov_tipo
        # A mensagem de aviso será renderizada no loop principal
    except ValueError:
        st.error("O ID da movimentação deve ser um número inteiro.")

def confirmar_exclusao_callback():
    mov_id = st.session_state.confirm_delete_id
    mov_tipo = st.session_state.confirm_delete_type

    if mov_id is None: # Não deveria acontecer se o botão for exibido apenas após o gatilho inicial
        st.error("Erro: Nenhuma movimentação para confirmar exclusão.")
        return

    try:
        if mov_tipo == "Entrada":
            estoque.excluir_entrada(mov_id)
            st.session_state.msg_sucesso = f"Entrada ID {mov_id} excluída e estoque revertido com sucesso! 🗑️"
        elif mov_tipo == "Saída":
            estoque.excluir_saida(mov_id)
            st.session_state.msg_sucesso = f"Saída ID {mov_id} excluída e estoque revertido com sucesso! 🗑️"
        
        # Limpa o estado de confirmação e recarrega a página
        st.session_state.confirm_delete_id = None
        st.session_state.confirm_delete_type = None
        st.session_state.gerenciar_id = "" # Limpa o campo de entrada
        st.rerun()
    except ValueError as e:
        st.error(f"Erro ao excluir: {e}")
    except Exception as e:
        st.error(f"Ocorreu um erro inesperado ao excluir: {e}")

def salvar_edicao_callback():
    record_id = st.session_state.editing_record_data['id']
    record_type = st.session_state.editing_record_type

    try:
        if record_type == "Entrada":
            # Coleta os valores atualizados das chaves do session state
            new_nome_produto = st.session_state.edit_entrada_nome_produto
            new_codigo_produto = st.session_state.edit_entrada_codigo_produto
            new_numero_pedido = st.session_state.edit_entrada_numero_pedido
            new_nome_cliente = st.session_state.edit_entrada_nome_cliente
            new_quantidade = st.session_state.edit_entrada_quantidade
            new_fornecedor = st.session_state.edit_entrada_fornecedor

            estoque.update_entrada(
                record_id,
                new_nome_produto,
                new_codigo_produto,
                new_numero_pedido,
                new_nome_cliente,
                new_quantidade,
                new_fornecedor
            )
            st.session_state.msg_sucesso = f"Entrada ID {record_id} atualizada com sucesso! 📝"

        elif record_type == "Saída":
            # Coleta os valores atualizados das chaves do session state
            new_numero_pedido = st.session_state.edit_saida_numero_pedido
            new_nome_cliente = st.session_state.edit_saida_nome_cliente
            new_quantidade_baixada = st.session_state.edit_saida_quantidade_baixada
            new_manuseio = st.session_state.edit_saida_manuseio
            new_retirado_por = st.session_state.edit_saida_retirado_por

            estoque.update_saida(
                record_id,
                new_numero_pedido,
                new_nome_cliente,
                new_quantidade_baixada,
                new_manuseio,
                new_retirado_por
            )
            st.session_state.msg_sucesso = f"Saída ID {record_id} atualizada com sucesso! 📝"
        
        # Limpa o estado de edição e recarrega a página
        st.session_state.show_edit_form = False
        st.session_state.editing_record_data = None
        st.session_state.editing_record_type = None
        st.session_state.gerenciar_id = "" # Limpa o campo de entrada
        st.rerun()

    except ValueError as e:
        st.error(f"Erro ao salvar alterações: {e}")
    except Exception as e:
        st.error(f"Ocorreu um erro inesperado ao salvar: {e}")

# Inicializa o banco de dados ao carregar a página
init_db()

# 1. Configuração Global (Layout Wide)
# Inicializa o banco de dados ao carregar a página
init_db()

# 1. Configuração Global (Layout Wide)
st.set_page_config(
    page_title="Controle De Estoque", 
    layout="wide",
)

# Exibição da Logo
st.image("logo.png", width=400)

# Exibe feedback visual se houver mensagem de sucesso pendente
if st.session_state.msg_sucesso:
    st.toast(st.session_state.msg_sucesso)
    st.session_state.msg_sucesso = None

# Estilização básica para o título
st.title("Controle de Estoque")
st.markdown("---")

# 2. Navegação via Tabs Nativas
tab1, tab2, tab3 = st.tabs([
    ":material/download: Registrar Entrada", 
    ":material/upload: Registrar Saída", 
    ":material/search: Painel / Consultas"
])

# --- ABA 1: REGISTRAR ENTRADA ---
with tab1:
    st.subheader("Nova Entrada de Mercadoria")
    st.caption("Utilize este formulário para vincular uma entrada de fornecedor diretamente a um pedido de venda.")

    # Container com borda para criar o efeito de "card"
    with st.container(border=True):
        with st.form("form_entrada_vinculada", border=False):
            # 3. Organização dos Campos (Grid)
            # Linha 1: Organizada para incluir o Código do Produto
            r1_col1, r1_col2, r1_col3 = st.columns([1, 1, 2]) # Proporção das colunas
            r1_col1.text_input("Nº Pedido de Venda", key="entrada_ped_venda", autocomplete="off")
            r1_col2.text_input("Código do Produto", key="entrada_prod_codigo", autocomplete="off")
            r1_col3.text_input("Nome do Produto", key="entrada_prod_nome", autocomplete="off")

            # Linha 2: Larga (3), Média (2), Estrita (1)
            r2_col1, r2_col2, r2_col3 = st.columns([3, 2, 1])
            r2_col1.text_input("Nome do Cliente", key="entrada_cliente_venda", autocomplete="off")
            r2_col2.text_input("Fornecedor", key="entrada_fornecedor", autocomplete="off")
            # Alterado para Inteiro: Removido format e step decimal, definido valor inicial como 0
            r2_col3.number_input("Quantidade", min_value=0, step=1, key="entrada_qtd_ent")

            # 4. Botão de Ação Primário com largura total
            st.form_submit_button("Registrar Entrada e Atualizar Estoque", type="primary", use_container_width=True, on_click=registrar_entrada_callback)

# --- ABA 2: BAIXA FRACIONADA (SAÍDA) ---
with tab2:
    st.header("Saída de Pedido / Fracionamento")
    
    # 1. Entrada do Número do Pedido (Trigger para o filtro dinâmico e para ser limpo)
    num_pedido = st.text_input("Número do Pedido", key="saida_num_pedido", help="Pressione Enter para carregar os dados do pedido.", autocomplete="off")

    if num_pedido:
        # Busca automática no banco de dados
        cliente_auto, produtos_pedido = estoque.get_detalhes_pedido(num_pedido)

        if not cliente_auto:
            st.warning(f"⚠️ Nenhum registro de entrada encontrado para o pedido '{num_pedido}'.")
        else:
            # 2. Preenchimento Automático do Cliente (Campo Desabilitado)
            st.text_input("Nome do Cliente", value=cliente_auto, disabled=True, autocomplete="off")

            if not produtos_pedido:
                st.error("Erro: Este pedido não possui produtos vinculados no estoque.")
            else:
                # 3. Lógica de Filtro Dinâmico: Selectbox exibe apenas o que pertence ao pedido
                dict_saida = {f"{p[1]} (Saldo: {int(p[2])} {p[3]})": p[0] for p in produtos_pedido}
                
                # Formulário para as seleções finais e execução da baixa
                with st.form("form_saida_final"):
                    st.selectbox("Produto para Baixa", options=dict_saida.keys(), key="saida_produto_sel")
                    
                    # Novos campos: Manuseio e Retirado Por organizados em colunas
                    col_m, col_r = st.columns(2)
                    col_m.text_input("Manuseio", key="saida_manuseio", autocomplete="off")
                    col_r.text_input("Retirado Por", key="saida_retirado_por", autocomplete="off")
                    
                    st.number_input("Quantidade de Saída", min_value=0, step=1, key="saida_qtd_saida")
                    
                    st.form_submit_button("Confirmar Baixa e Registrar Saída", type="primary", on_click=dar_baixa_callback, args=(dict_saida, cliente_auto))
    else:
        st.info("💡 Informe o Número do Pedido acima para carregar os produtos disponíveis para baixa.")

# --- ABA 3: PAINEL / CONSULTAS ---
with tab3:
    st.header("Resumo do Estoque Atual")
    saldo_data = estoque.listar_saldo_estoque()
    if saldo_data:
        df_saldo = pd.DataFrame(saldo_data, columns=["ID", "Pedido", "Cliente", "Nome", "Código", "Quantidade Atual", "Unidade"])
        df_saldo = df_saldo.drop(columns=["ID"])
        st.dataframe(df_saldo, use_container_width=True, hide_index=True)
    
    st.divider()
    st.header("Histórico Detalhado de Entradas")
    h_entradas = estoque.get_historico_entradas()
    if h_entradas:
        ver_tudo_ent = st.checkbox("Expandir histórico de entradas (Ver tudo)", key="ver_tudo_ent")
        dados_exibicao_ent = h_entradas if ver_tudo_ent else h_entradas[:5]
        df_ent = pd.DataFrame(dados_exibicao_ent, columns=["ID", "Produto", "Código", "Pedido", "Cliente", "Quantidade", "Fornecedor", "Data"])
        st.dataframe(df_ent, use_container_width=True, hide_index=True)
    else:
        st.info("Nenhuma entrada registrada ainda.")

    st.divider()
    st.header("Histórico de Saídas")
    historico = estoque.get_historico_saidas()
    if historico:
        ver_tudo_sai = st.checkbox("Expandir histórico de saídas (Ver tudo)", key="ver_tudo_sai")
        dados_exibicao_sai = historico if ver_tudo_sai else historico[:5]
        df_hist = pd.DataFrame(dados_exibicao_sai, columns=["ID", "Produto", "Pedido", "Cliente", "Qtd Baixada", "Manuseio", "Retirado Por", "Data/Hora", "Unidade"])
        st.dataframe(df_hist, use_container_width=True, hide_index=True)
    else:
        st.info("Nenhuma saída registrada ainda.")

    st.divider()
    st.header("Gerenciar Movimentações (Editar/Excluir)")
    with st.expander("Ações do Pedido / Movimentação", expanded=False):
        col_id, col_tipo = st.columns([0.7, 0.3])
        with col_id:
            st.text_input("ID da Movimentação (Entrada ou Saída)", key="gerenciar_id", help="Insira o ID da entrada ou saída que deseja gerenciar.")
        with col_tipo:
            st.radio("Tipo", ["Entrada", "Saída"], key="gerenciar_tipo", horizontal=True)
        
        col_load, col_delete = st.columns(2)
        with col_load:
            st.button("Carregar para Editar", type="primary", on_click=carregar_para_edicao_callback, use_container_width=True)
        with col_delete:
            st.button("Excluir Movimentação", type="secondary", on_click=iniciar_exclusao_callback, use_container_width=True)

        # Confirmação para exclusão
        if st.session_state.confirm_delete_id is not None:
            st.warning(f"Tem certeza que deseja excluir a {st.session_state.confirm_delete_type} ID {st.session_state.confirm_delete_id}? Esta ação é irreversível e ajustará o estoque.")
            col_confirm_del, col_cancel_del = st.columns(2)
            with col_confirm_del:
                st.button("Confirmar Exclusão", type="primary", on_click=confirmar_exclusao_callback, use_container_width=True)
            with col_cancel_del:
                if st.button("Cancelar", type="secondary", use_container_width=True):
                    st.session_state.confirm_delete_id = None
                    st.session_state.confirm_delete_type = None
                    st.rerun()

        # Formulário de Edição
        if st.session_state.show_edit_form and st.session_state.editing_record_data:
            record = st.session_state.editing_record_data
            record_type = st.session_state.editing_record_type
            st.subheader(f"Editando {record_type} ID {record['id']}")

            with st.form(key=f"edit_form_{record_type}", border=True):
                if record_type == "Entrada":
                    st.text_input("Nome do Produto", value=record['nome_produto'], key="edit_entrada_nome_produto")
                    st.text_input("Código do Produto", value=record['codigo_produto'], key="edit_entrada_codigo_produto")
                    st.text_input("Nº Pedido de Venda", value=record['numero_pedido'], key="edit_entrada_numero_pedido")
                    st.text_input("Nome do Cliente", value=record['nome_cliente'], key="edit_entrada_nome_cliente")
                    st.number_input("Quantidade", value=float(record['quantidade']), step=0.01, key="edit_entrada_quantidade")
                    st.text_input("Fornecedor", value=record['fornecedor'], key="edit_entrada_fornecedor")
                elif record_type == "Saída":
                    # Para Saída, nome/código do produto são do JOIN, não diretamente da tabela 'saidas'
                    # Exibi-los, mas não permitir edição, pois produto_id é fixo para a saída
                    st.text_input("Produto (Não Editável)", value=record['produto_nome'], disabled=True)
                    st.text_input("Código do Produto (Não Editável)", value=record['produto_codigo'], disabled=True)
                    st.text_input("Nº Pedido", value=record['numero_pedido'], key="edit_saida_numero_pedido")
                    st.text_input("Nome do Cliente", value=record['nome_cliente'], key="edit_saida_nome_cliente")
                    st.number_input("Quantidade Baixada", value=float(record['quantidade_baixada']), step=0.01, key="edit_saida_quantidade_baixada")
                    st.text_input("Manuseio", value=record['manuseio'], key="edit_saida_manuseio")
                    st.text_input("Retirado Por", value=record['retirado_por'], key="edit_saida_retirado_por")
                
                col_save, col_cancel_edit = st.columns(2)
                with col_save:
                    st.form_submit_button("Salvar Alterações", type="primary", on_click=salvar_edicao_callback, use_container_width=True)
                with col_cancel_edit:
                    if st.form_submit_button("Cancelar Edição", type="secondary", use_container_width=True):
                        st.session_state.show_edit_form = False
                        st.session_state.editing_record_data = None
                        st.session_state.editing_record_type = None
                        st.session_state.gerenciar_id = ""
                        st.rerun()

    st.divider() # Adiciona um divisor após a nova seção de gerenciamento