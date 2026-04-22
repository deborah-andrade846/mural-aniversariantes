import streamlit as st
from supabase import create_client, Client
import datetime
import uuid
from utils import get_supabase, to_bool, carregar_config, hash_senha, verificar_senha

st.set_page_config(page_title="Cadastro no Mural", page_icon="📝")

supabase = get_supabase()

# --- CONTROLE DE ACESSO ---
config = carregar_config()
if not to_bool(config.get("liberar_cadastro", True)):
    st.warning("### ⏳ Período de cadastro encerrado ou ainda não iniciado.")
    st.stop()

# --- UI ---
st.title("📝 Atualizar Perfil no Mural")
st.write("Adicione sua foto, uma curiosidade e proteja seu perfil com uma senha.")

try:
    with st.spinner("Carregando lista de colaboradores..."):
        res = supabase.table("aniversariantes").select("nome, perfil_completo").execute()
    lista_funcionarios = res.data or []

except Exception as e:
    st.error("Não foi possível conectar ao banco de dados. Tente novamente em instantes.")
    st.stop()

# Ordena alfabeticamente
nomes_disponiveis = sorted([f["nome"] for f in lista_funcionarios])
opcoes_lista = ["", "➕ Meu nome não está na lista"] + nomes_disponiveis

nome_selecionado = st.selectbox("Selecione seu nome na lista oficial:", opcoes_lista)

# --- NOVO CADASTRO ---
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
        senha_confirm = st.text_input("Confirme sua senha", type="password")
        curiosidade = st.text_area("Sua curiosidade (hobby, comida favorita...)", max_chars=200)
        foto_upload = st.file_uploader("Sua foto (Opcional)", type=["jpg", "png", "jpeg"])

        submit_novo = st.form_submit_button("✅ Criar meu Perfil")

        if submit_novo:
            if not novo_nome.strip():
                st.error("⚠️ O nome é obrigatório.")
            elif not senha_acesso:
                st.error("⚠️ A senha é obrigatória.")
            elif senha_acesso != senha_confirm:
                st.error("❌ As senhas não coincidem.")
            else:
                try:
                    foto_url = ""
                    if foto_upload:
                        with st.spinner("Enviando foto..."):
                            ext = foto_upload.name.split('.')[-1]
                            nome_arq = f"{uuid.uuid4()}.{ext}"
                            supabase.storage.from_("fotos_mural").upload(nome_arq, foto_upload.getvalue())
                            foto_url = supabase.storage.from_("fotos_mural").get_public_url(nome_arq)

                    dados_insert = {
                        "nome":            novo_nome.strip(),
                        "data_nascimento": str(nova_data),
                        "curiosidade":     curiosidade,
                        "senha_perfil":    hash_senha(senha_acesso),
                        "perfil_completo": True,
                        "foto_url":        foto_url,
                    }
                    supabase.table("aniversariantes").insert(dados_insert).execute()
                    st.success(f"✅ Cadastro de **{novo_nome.strip()}** criado com sucesso! Bem-vindo(a) à equipe. 🎉")

                except Exception as e:
                    st.error("Erro ao salvar seu perfil. Tente novamente.")

# --- ATUALIZAÇÃO ---
elif nome_selecionado != "":
    dados_atuais = next(item for item in lista_funcionarios if item["nome"] == nome_selecionado)
    foi_completado = to_bool(dados_atuais.get("perfil_completo", False))

    with st.form("form_update"):
        st.write(f"### Olá, {nome_selecionado.split()[0]}! 👋")

        if foi_completado:
            st.warning("🔒 Este perfil já foi preenchido. Para editar, insira sua senha de perfil.")
        else:
            st.info("✨ Seu perfil ainda está básico. Vamos completá-lo? Crie uma senha para protegê-lo.")

        senha_acesso = st.text_input(
            "Senha do seu perfil" if foi_completado else "Crie uma senha para seu perfil",
            type="password"
        )

        # Permite atualizar data de nascimento se estiver com ano fictício (1900)
        data_atual_raw = None
        try:
            res_data = supabase.table("aniversariantes").select("data_nascimento").eq("nome", nome_selecionado).single().execute()
            data_atual_raw = res_data.data.get("data_nascimento") if res_data.data else None
        except Exception:
            pass

        mostrar_campo_data = data_atual_raw and str(data_atual_raw).startswith("1900")
        if mostrar_campo_data:
            st.info("📅 Seu aniversário está com o ano fictício. Aproveite para corrigir!")
            nova_data = st.date_input(
                "Sua Data de Nascimento",
                min_value=datetime.date(1940, 1, 1),
                max_value=datetime.date.today(),
                format="DD/MM/YYYY"
            )
        
        if not foi_completado:
            senha_confirm = st.text_input("Confirme sua senha", type="password")

        curiosidade = st.text_area("Sua curiosidade", max_chars=200)
        foto_upload = st.file_uploader("Sua foto", type=["jpg", "png", "jpeg"])

        submit_update = st.form_submit_button("💾 Salvar Informações")

        if submit_update:
            try:
                res_check = supabase.table("aniversariantes").select("senha_perfil").eq("nome", nome_selecionado).single().execute()
                senha_no_banco = res_check.data.get("senha_perfil") if res_check.data else None

                if foi_completado and not verificar_senha(senha_acesso, senha_no_banco):
                    st.error("❌ Senha incorreta! Você não tem permissão para alterar este perfil.")
                elif not senha_acesso:
                    st.error("⚠️ Você precisa definir uma senha para seu perfil.")
                elif not foi_completado and senha_acesso != senha_confirm:
                    st.error("❌ As senhas não coincidem.")
                else:
                    foto_url = ""
                    if foto_upload:
                        with st.spinner("Enviando foto..."):
                            ext = foto_upload.name.split('.')[-1]
                            nome_arq = f"{uuid.uuid4()}.{ext}"
                            supabase.storage.from_("fotos_mural").upload(nome_arq, foto_upload.getvalue())
                            foto_url = supabase.storage.from_("fotos_mural").get_public_url(nome_arq)

                    dados_update = {
                        "curiosidade":     curiosidade,
                        "senha_perfil":    hash_senha(senha_acesso),
                        "perfil_completo": True,
                    }
                    if foto_url:
                        dados_update["foto_url"] = foto_url
                    if mostrar_campo_data:
                        dados_update["data_nascimento"] = str(nova_data)

                    supabase.table("aniversariantes").update(dados_update).eq("nome", nome_selecionado).execute()
                    st.success("✅ Perfil atualizado e protegido com sucesso!")

            except Exception as e:
                st.error("Erro ao atualizar o perfil. Tente novamente.")
