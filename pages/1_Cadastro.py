import streamlit as st
from supabase import create_client, Client
import datetime
import uuid

st.set_page_config(page_title="Cadastro no Mural", page_icon="📝")

# Conexão com o banco
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

st.title("📌 Preencha seu perfil para o Mural")
st.write("Deixe sua marca no nosso quadro de aniversariantes!")

with st.form("cadastro_form", clear_on_submit=True):
    nome = st.text_input("Nome Completo")
    
    data_nasc = st.date_input(
        "Data de Nascimento",
        min_value=datetime.date(1940, 1, 1),
        max_value=datetime.date.today(),
        format="DD/MM/YYYY"
    )
    
    curiosidade = st.text_area("Uma curiosidade sobre você (Ex: Hobby, comida favorita...)")
    
    # NOVO: Botão de Upload nativo
    foto_upload = st.file_uploader("Faça upload de uma foto sua (Opcional)", type=["jpg", "jpeg", "png"])
    
    submit = st.form_submit_button("Enviar para o Mural")

    if submit:
        if nome and data_nasc:
            try:
                foto_url = ""
                
                # Se o usuário anexou uma foto
                if foto_upload is not None:
                    # 1. Gera um nome único para o arquivo (ex: 8f72a-foto.jpg)
                    extensao = foto_upload.name.split('.')[-1]
                    nome_arquivo = f"{uuid.uuid4()}.{extensao}"
                    
                    # 2. Lê os dados da imagem
                    file_bytes = foto_upload.getvalue()
                    
                    # 3. Faz o upload direto para o Storage do Supabase (Bucket 'fotos_mural')
                    supabase.storage.from_("fotos_mural").upload(
                        path=nome_arquivo,
                        file=file_bytes,
                        file_options={"content-type": foto_upload.type}
                    )
                    
                    # 4. Pega o link público automático que o Supabase gerou
                    foto_url = supabase.storage.from_("fotos_mural").get_public_url(nome_arquivo)

                # Monta os dados para a tabela
                novo_dado = {
                    "nome": nome,
                    "data_nascimento": str(data_nasc),
                    "curiosidade": curiosidade,
                    "foto_url": foto_url
                }
                
                # Envia para a tabela
                resposta = supabase.table("aniversariantes").insert(novo_dado).execute()
                st.success("✅ Cadastro realizado com sucesso! Verifique a aba do Mural.")
                
            except Exception as e:
                # Caso de erro (como o APIError), ele mostrará o motivo exato na tela
                st.error(f"❌ Erro de comunicação com o banco: {e}")
                
        else:
            st.error("⚠️ Por favor, preencha pelo menos o nome e a data de nascimento.")
