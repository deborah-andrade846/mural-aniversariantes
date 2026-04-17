import streamlit as st
from supabase import create_client, Client
import datetime # <-- Adicione esta linha

st.set_page_config(page_title="Cadastro no Mural", page_icon="📝")

# Conectando ao banco de dados
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

st.title("📌 Preencha seu perfil para o Mural")
st.write("Deixe sua marca no nosso quadro de aniversariantes!")

# Criando o formulário
with st.form("cadastro_form", clear_on_submit=True):
    nome = st.text_input("Nome Completo")
    # Apague o data_nasc antigo e coloque este:
    data_nasc = st.date_input(
        "Data de Nascimento",
        min_value=datetime.date(1940, 1, 1),
        max_value=datetime.date.today(),
        format="DD/MM/YYYY"
    )
    curiosidade = st.text_area("Uma curiosidade sobre você (Ex: Hobby, comida favorita...)")
    
    # Para simplificar essa primeira versão, usaremos um link de foto. 
    # Depois podemos evoluir para upload de arquivo direto no Supabase Storage.
    foto_url = st.text_input("Link de uma foto sua (Opcional - deixe vazio para avatar padrão)")
    
    submit = st.form_submit_button("Enviar para o Mural")

    if submit:
        if nome and data_nasc:
            # Organiza os dados e envia para o Supabase
            novo_dado = {
                "nome": nome,
                "data_nascimento": str(data_nasc),
                "curiosidade": curiosidade,
                "foto_url": foto_url
            }
            resposta = supabase.table("aniversariantes").insert(novo_dado).execute()
            st.success("✅ Cadastro realizado com sucesso! Verifique a aba do Mural.")
        else:
            st.error("⚠️ Por favor, preencha pelo menos o nome e a data de nascimento.")