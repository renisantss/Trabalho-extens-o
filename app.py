import streamlit as st
import json
import os
import base64
import urllib.parse
import uuid
from supabase import create_client

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Catálogo Isabelle", page_icon="🛍️")

PASTA_ATUAL = os.path.dirname(os.path.abspath(__file__))
ARQUIVO_DADOS = os.path.join(PASTA_ATUAL, "produtos.json")
FOTO_PADRAO = "https://via.placeholder.com/400?text=Sem+Foto"
TELEFONE_WHATSAPP = "5521976885347" 
SENHA_ADMIN = "0611"
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

BUCKET = "catalogo-fotos"
# 2. FUNÇÕES PERSISTÊNCIA
def converter_imagem_para_base64(uploaded_file):
    if uploaded_file is not None:
        bytes_data = uploaded_file.getvalue()
        tipo_mime = uploaded_file.type

        extensao = uploaded_file.name.rsplit(".", 1)[-1].lower()
        nome_arquivo = f"produtos/{uuid.uuid4()}.{extensao}"

        supabase.storage.from_(BUCKET).upload(
            nome_arquivo,
            bytes_data,
            file_options={"content-type": tipo_mime}
        )

        return supabase.storage.from_(BUCKET).get_public_url(nome_arquivo)

    return FOTO_PADRAO

def carregar_produtos():
    resposta = supabase.table("produtos").select("*").execute()

    produtos = []

    for item in resposta.data:
        produtos.append({
            "id": item["id"],
            "nome": item["nome"],
            "categoria": item["categoria"],
            "preco": float(item["preco"]),
            "imagem": item.get("imagem_url") or FOTO_PADRAO
        })

    return produtos

def salvar_produtos(lista_produtos):
    resposta = supabase.table("produtos").select("id").execute()
    ids_existentes = {item["id"] for item in resposta.data}

    ids_atualizados = set()

    for produto in lista_produtos:
        produto_id = produto.get("id") or str(uuid.uuid4())
        produto["id"] = produto_id

        dados = {
            "id": produto_id,
            "nome": produto["nome"],
            "categoria": produto["categoria"],
            "preco": float(produto["preco"]),
            "imagem_url": produto.get("imagem", FOTO_PADRAO)
        }

        supabase.table("produtos").upsert(dados).execute()
        ids_atualizados.add(produto_id)

    for produto_id in ids_existentes - ids_atualizados:
        supabase.table("produtos").delete().eq("id", produto_id).execute()

# LEITURA MEMÓRIA/JSON
if "produtos" not in st.session_state:
    st.session_state.produtos = carregar_produtos()

st.title("🦋 Catálogo Isabelle")
aba = st.sidebar.radio("Navegação", ["Ver Catálogo (Cliente)", "Painel de Gestão (Isabelle)"])

# --- ABA DO CLIENTE ---
if aba == "Ver Catálogo (Cliente)":
    st.subheader("Selecione a categoria desejada:")
    
    cat = st.selectbox(
      "Selecione uma categoria:",
      ["Unhas", "Joias", "Móveis", "Todas"],
      key="categoria_cliente_v3"
    )
# Campo de texto livre (sem lista de opções)
    busca = st.text_input(
    "🔍 Pesquisar produto:",
    placeholder="Digite o nome do produto...",
    key="busca_texto_livre"
    )
    # 1. Filtra pela categoria (com opção "Todas" para facilitar a busca geral)
    if cat == "Todas":
        itens_filtrados = st.session_state.produtos
    else:
        itens_filtrados = [
            p for p in st.session_state.produtos
            if str(p.get("categoria", "")).strip().casefold()
            == str(cat).strip().casefold()
        ]
    
    # 2. Filtra pelo que a pessoa digitou (ignora maiúsculas/minúsculas e espaços)
    termo_busca = busca.strip().casefold()
    if termo_busca:
        itens_filtrados = [
            p for p in itens_filtrados
            if termo_busca in str(p.get("nome", "")).casefold()
        ]
    
    st.divider()
       
    if itens_filtrados:
     for item in itens_filtrados:
            nome = item.get("nome", "")
            preco = float(item.get("preco", 0.0))
            imagem = item.get("imagem", FOTO_PADRAO)
           
            st.image(imagem, use_container_width=True)
            st.write(f"**{nome}**")
            st.write(f"Preço: R$ {preco:.2f}")

            cat_item = str(item.get("categoria", "")).strip().casefold()
            if cat == "Unhas":
                mensagem = (
                    f"Olá! Tenho interesse no serviço '{nome}', "
                    f"no valor de R$ {preco:.2f}. "
                    "Gostaria de saber os horários disponíveis para agendar."
                )
            else:
                mensagem = (
                    f"Olá! Vi o item '{nome}' por "
                    f"R$ {preco:.2f} no catálogo e gostaria de comprar."
                )

            mensagem_url = urllib.parse.quote(mensagem)
            link_whatsapp = (
                f"https://wa.me/{TELEFONE_WHATSAPP}?text={mensagem_url}"
            )

            st.link_button("💬 Comprar", link_whatsapp)
            st.write("---")
    else:
       st.info("Nenhum item encontrado.")


# --- ABA DA DONA (PAINEL ADMINISTRATIVO) ---
elif aba == "Painel de Gestão (Isabelle)":
    st.subheader("🔒 Área Restrita - Administração")
    
    senha = st.text_input("Digite a senha de acesso:", type="password")
    
    if senha == SENHA_ADMIN:
        st.success("Acesso liberado!")
        
        st.divider()
        
        aba1, aba2 = st.tabs(["➕ Cadastrar Novo Item", "⚙️ Gerenciar / Editar / Excluir"])
        
        # 1. CADASTRAR
        with aba1:
            nome = st.text_input("Nome do Item")
            categoria = st.selectbox("Categoria", ["Unhas", "Joias", "Móveis"])
            preco = st.number_input("Preço (R$)", min_value=0.0, step=5.0)
            
            arquivo_foto = st.file_uploader("Carregar foto", type=["png", "jpg", "jpeg", "webp"])
            
            if st.button("Salvar no Catálogo"):
                if nome:
                    imagem_salva = converter_imagem_para_base64(arquivo_foto)
                    novo_item = {
                        "nome": nome.strip(),
                        "categoria": categoria.strip(),
                        "preco": float(preco),
                        "imagem": imagem_salva
                    }
                    st.session_state.produtos.append(novo_item)
                    salvar_produtos(st.session_state.produtos)
                    st.success(f"'{nome}' cadastrado com sucesso!")
                    st.rerun()
                else:
                    st.warning("Por favor, digite o nome do produto.")
                    
        # 2. GERENCIAR (EDITAR / EXCLUIR)
        with aba2:
            if st.session_state.produtos:
                nomes_produtos = {
                    f"{i + 1} - {p['nome']} (R$ {p['preco']:.2f})": i 
                    for i, p in enumerate(st.session_state.produtos)
                }
                
                produto_selecionado_nome = st.selectbox(
                    "Selecione um item para alterar:", 
                    list(nomes_produtos.keys()), 
                    key="select_prod"
                )
                
                idx_sel = nomes_produtos[produto_selecionado_nome]
                item_sel = st.session_state.produtos[idx_sel]
                
                st.write("---")
                st.write("**Editar Dados:**")

                # Form perfeitamente aninhado com o escopo do item
                with st.form(key=f"form_edit_{idx_sel}"): 
                    novo_nome = st.text_input("Nome", value=item_sel["nome"])
                    cat_atual = str(item_sel["categoria"]).strip()
                    cat_idx = ["Unhas", "Joias", "Móveis"].index(cat_atual) if cat_atual in ["Unhas", "Joias", "Móveis"] else 0
                    nova_cat = st.selectbox("Categoria", ["Unhas", "Joias", "Móveis"], index=cat_idx)
                    novo_preco = st.number_input("Preço (R$)", min_value=0.0, value=float(item_sel["preco"]), step=5.0)
                    arquivo_foto_edicao = st.file_uploader(
                    "Alterar foto do produto",
                    type=["png", "jpg", "jpeg", "webp"],
                    key=f"foto_edit_{idx_sel}"
                    )
                    submitted = st.form_submit_button("💾 Salvar Alterações", type="primary")
                    if submitted:

                      # Mantém a foto antiga se nenhuma nova for enviada
                      if arquivo_foto_edicao is not None:
                       imagem_atualizada = converter_imagem_para_base64(
                         arquivo_foto_edicao
                       )
                      else:
                        imagem_atualizada = item_sel.get("imagem", FOTO_PADRAO)

                      st.session_state.produtos[idx_sel] = {
                        "nome": novo_nome.strip(),
                        "categoria": nova_cat.strip(),
                        "preco": float(novo_preco),
                        "imagem": imagem_atualizada,
                        "id": item_sel["id"]
                      }

                      salvar_produtos(st.session_state.produtos)
                      st.success("Produto atualizado com sucesso!")
                      st.rerun()
                st.write("---")
                if st.button("🗑️ Excluir Item", key=f"btn_del_{idx_sel}"):
                    st.session_state.produtos.pop(idx_sel)
                    salvar_produtos(st.session_state.produtos)
                    st.warning("Item removido do catálogo!")
                    st.rerun()
            else:
                st.info("Nenhum produto cadastrado para gerenciar.")
                
    elif senha != "":
        st.error("Senha incorreta!")