# Lista principal que funciona como banco de dados na memória
catalogo = []

def cadastrar_item(nome, categoria, preco):
    item = {
        "nome": nome.strip(),
        "categoria": categoria.strip(),
        "preco": float(preco)
    }
    catalogo.append(item)
    print(f"✅ '{nome}' cadastrado com sucesso!")

def listar_por_categoria(cat_desejada):
    print(f"\n--- 🛍️ CATÁLOGO DE {cat_desejada.upper()} ---")
    encontrados = [item for item in catalogo if item["categoria"].lower() == cat_desejada.lower()]
    
    if not encontrados:
        print("Nenhum item encontrado nesta categoria.")
    else:
        for item in encontrados:
            print(f"• {item['nome']} - R$ {item['preco']:.2f}")

# --- TESTANDO AS FUNÇÕES ---
cadastrar_item("Anel Perolado", "Joias", 119.90)
cadastrar_item("Beliche vegas + 2 colchões solteiro d20", "Móveis", 960.00)
cadastrar_item("Aplicação de Gel", "Unhas", 100.00)
cadastrar_item("Manicure Simples", "Unhas", 45.00)

# Filtrando os resultados
listar_por_categoria("Unhas")
listar_por_categoria("Joias")