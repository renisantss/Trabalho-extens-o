
import json
import base64
import uuid
import streamlit as st
from supabase import create_client

st.title("Migração do Catálogo Isabelle")

BUCKET = "catalogo-fotos"

try:
    url = st.secrets["SUPABASE_URL"]
    chave = st.secrets["SUPABASE_KEY"]

    supabase = create_client(url, chave)

    with open("produtos.json", "r", encoding="utf-8") as arquivo:
        produtos = json.load(arquivo)

    enviados = 0
    atualizados = 0

    for produto in produtos:
        nome = produto["nome"].strip()
        categoria = produto["categoria"].strip()
        preco = produto.get("preco", produto.get("preço"))
        imagem = produto.get("imagem", "")

        imagem_url = ""

        # Se já existe uma URL, aproveita o endereço
        if isinstance(imagem, str) and imagem.startswith("http"):
            imagem_url = imagem

        # Se a imagem está em Base64, envia ao Storage
        elif isinstance(imagem, str) and imagem:
            if imagem.startswith("data:"):
                cabecalho, dados = imagem.split(",", 1)
                tipo = cabecalho.split(";")[0].replace("data:", "")
            else:
                dados = imagem
                tipo = "image/jpeg"

            if dados and "base64" in imagem or imagem.startswith("data:"):
                conteudo = base64.b64decode(dados)

                extensao = {
                    "image/jpeg": "jpg",
                    "image/png": "png",
                    "image/webp": "webp"
                }.get(tipo, "jpg")

                caminho = f"produtos/{uuid.uuid4()}.{extensao}"

                supabase.storage.from_(BUCKET).upload(
                    caminho,
                    conteudo,
                    file_options={"content-type": tipo}
                )

                imagem_url = supabase.storage.from_(
                    BUCKET
                ).get_public_url(caminho)

        dados_produto = {
            "nome": nome,
            "categoria": categoria,
            "preco": preco,
            "imagem_url": imagem_url
        }

        # Evita duplicar produtos em uma segunda execução
        existente = (
            supabase.table("produtos")
            .select("id")
            .eq("nome", nome)
            .eq("categoria", categoria)
            .limit(1)
            .execute()
        )

        if existente.data:
            supabase.table("produtos").update(
                dados_produto
            ).eq("id", existente.data[0]["id"]).execute()

            atualizados += 1
        else:
            supabase.table("produtos").insert(
                dados_produto
            ).execute()

            enviados += 1

    st.success("Migração concluída!")
    st.write(f"Novos produtos: {enviados}")
    st.write(f"Produtos atualizados: {atualizados}")

except Exception as erro:
    st.error("Erro durante a migração:")
    st.write(str(erro))
