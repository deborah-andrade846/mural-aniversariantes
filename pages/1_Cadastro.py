import streamlit as st
from supabase import create_client, Client
import datetime
import uuid
if not st.session_state.get('liberar_cadastro', True):
    st.warning("### Período de cadastro encerrado ou ainda não iniciado.")
    st.stop()
st.set_page_config(page_title="Cadastro no Mural", page_icon="📝")

# Conexão
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

st.title("📝 Atualizar Perfil no Mural")

try:
    # 1. Busca a lista de todos os nomes cadastrados para o Selectbox
    res = supabase.table("aniversariantes").select("nome, perfil_completo").execute()
    lista_funcionarios = res.data
    nomes_disponiveis = [f["nome"] for f in lista_funcionarios]

    # Adiciona a opção de criar um novo logo no início da lista
    opcoes_lista = ["", "➕ Meu nome não está na lista"] + nomes_disponiveis

    nome_selecionado = st.selectbox("Selecione seu nome na lista oficial:", opcoes_lista)

    # --- CENÁRIO 1: O FUNCIONÁRIO É NOVO E PRECISA SER CRIADO DO ZERO ---
    if nome_selecionado == "➕ Meu nome não está na lista":
        with st.form("form_novo"):
            st.info("👋 Bem-vindo(a)! Como você é novo por aqui, vamos criar seu cadastro do zero.")
            
            novo_nome = st.text_input("Seu Nome Completo")
            nova_data = st.date_input(
                "Sua Data de Nascimento",
                min_value=datetime.date(1940, 1, 1),
                max_value=datetime.date.today(),
                format="DD/MM/YYYY"
            )
            senha_acesso = st.text_input("Crie uma senha para proteger seu perfil", type="password")
            curiosidade = st.text_area("Sua curiosidade (Hobby, comida favorita...)")
            foto_upload = st.file_uploader("Sua foto (Opcional)", type=["jpg", "png", "jpeg"])
            
            submit_novo = st.form_submit_button("Criar meu Perfil")

            if submit_novo:
                if not novo_nome or not senha_acesso:
                    st.error("⚠️ Nome e Senha são obrigatórios para criar o perfil!")
                else:
                    foto_url = ""
                    if foto_upload:
                        ext = foto_upload.name.split('.')[-1]
                        nome_arq = f"{uuid.uuid4()}.{ext}"
                        supabase.storage.from_("fotos_mural").upload(nome_arq, foto_upload.getvalue())
                        foto_url = supabase.storage.from_("fotos_mural").get_public_url(nome_arq)

                    dados_insert = {
                        "nome": novo_nome,
                        "data_nascimento": str(nova_data),
                        "curiosidade": curiosidade,
                        "senha_perfil": senha_acesso,
                        "perfil_completo": True,
                        "foto_url": foto_url
                    }

                    # INSERT (Cria uma linha nova no banco)
                    supabase.table("aniversariantes").insert(dados_insert).execute()
                    st.success(f"✅ Cadastro de {novo_nome} criado com sucesso! Bem-vindo(a) à equipe.")


    # --- CENÁRIO 2: O NOME JÁ ESTÁ NA LISTA OFICIAL ---
    elif nome_selecionado != "":
        dados_atuais = next(item for item in lista_funcionarios if item["nome"] == nome_selecionado)
        foi_completado = dados_atuais.get("perfil_completo", False)

        with st.form("form_update"):
            st.write(f"### Olá, {nome_selecionado}!")
            
            # Trava de Segurança
            if foi_completado:
                st.warning("🔒 Este perfil já foi preenchido. Para editar, insira sua senha de perfil.")
                senha_acesso = st.text_input("Senha do seu perfil", type="password")
            else:
                st.info("✨ Seu perfil ainda está básico. Vamos completá-lo? Crie uma senha para protegê-lo.")
                senha_acesso = st.text_input("Crie uma senha para seu perfil", type="password")

            curiosidade = st.text_area("Sua curiosidade")
            foto_upload = st.file_uploader("Sua foto", type=["jpg", "png", "jpeg"])
            
            submit_update = st.form_submit_button("Salvar Informações")

            if submit_update:
                res_check = supabase.table("aniversariantes").select("senha_perfil").eq("nome", nome_selecionado).single().execute()
                senha_no_banco = res_check.data.get("senha_perfil") if res_check.data else None

                # Validação da senha
                if foi_completado and senha_acesso != senha_no_banco:
                    st.error("❌ Senha incorreta! Você não tem permissão para alterar este perfil.")
                elif not senha_acesso:
                    st.error("⚠️ Você precisa definir uma senha para seu perfil.")
                else:
                    foto_url = ""
                    if foto_upload:
                        ext = foto_upload.name.split('.')[-1]
                        nome_arq = f"{uuid.uuid4()}.{ext}"
                        supabase.storage.from_("fotos_mural").upload(nome_arq, foto_upload.getvalue())
                        foto_url = supabase.storage.from_("fotos_mural").get_public_url(nome_arq)

                    dados_update = {
                        "curiosidade": curiosidade,
                        "senha_perfil": senha_acesso,
                        "perfil_completo": True
                    }
                    if foto_url:
                        dados_update["foto_url"] = foto_url

                    # UPDATE (Atualiza o perfil existente)
                    supabase.table("aniversariantes").update(dados_update).eq("nome", nome_selecionado).execute()
                    st.success("✅ Perfil atualizado e protegido com sucesso!")

except Exception as e:
    st.error(f"Erro ao carregar dados: {e}")
