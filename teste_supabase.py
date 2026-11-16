import streamlit as st
from supabase import create_client

st.title("Teste Supabase")

url = st.secrets["SUPABASE_URL"]
chave = st.secrets["SUPABASE_KEY"]

supabase = create_client(url, chave)

resposta = supabase.table("produtos").select("*").limit(1).execute()

st.success("Conexão com Supabase funcionando!")
st.write("Banco de dados acessado com sucesso.")