import streamlit as st
from supabase import create_client, Client
import datetime
import uuid

st.set_page_config(page_title="Cadastro no Mural", page_icon="📝")

# --- CONEXÃO ---
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

# --- UTILITÁRIOS ---
def to_bool(val, default=False):
    """Converte valores do Supabase (string/bool) para booleano Python."""
    if isinstance(val, bool):
        return val
    if isinstance(val, str):
        return val.strip().lower() in ('true', '1', 'yes', 'sim')
    return default

def carregar_config():
    try:
        resp = supabase.table("configuracoes_mural").select("*").execute()
        return {item['chave']: item['valor'] for item in resp.data}
    except Exception:
        return {}

config = carregar_config()

# --- CONTROLE DE ACESSO ---
if not to_bool(config.get("liberar_cadastro", True)):
    st.warning("### ⏳ Período de cadastro encerrado ou ainda não iniciado.")
    st.stop()

# --- UI ---
st.title("📝 Atualizar Perfil no Mural")
st.write("Adicione sua foto, uma curiosidade e proteja seu perfil com uma senha.")

try:
    res = supabase.table("aniversariantes").select("nome, perfil_completo").execute()
    lista_funcionarios = res.data or []
    nomes_disponiveis  = [f["nome"] for f in lista_funcionarios]

    opcoes_lista = ["", "➕ Meu nome não está na lista"] + nomes_disponiveis

    nome_selecionado = st.selectbox("Selecione seu nome na lista oficial:", opcoes_lista)

    # --- NOVO CADASTRO ---
    if nome_selecionado == "➕ Meu nome não está na lista":
        with st.form("form_novo"):
            st.info("👋 Bem-vindo(a)! Como você é novo por aqui, vamos criar seu cadastro do zero.")

            novo_nome  = st.text_input("Seu Nome Completo")
            nova_data  = st.date_input(
                "Sua Data de Nascimento",
                min_value=datetime.date(1940, 1, 1),
                max_value=datetime.date.today(),
                format="DD/MM/YYYY"
            )
            senha_acesso  = st.text_input("Crie uma senha para proteger seu perfil", type="password")
            curiosidade   = st.text_area("Sua curiosidade (hobby, comida favorita...)", max_chars=200)
            foto_upload   = st.file_uploader("Sua foto (Opcional)", type=["jpg", "png", "jpeg"])

            submit_novo = st.form_submit_button("✅ Criar meu Perfil")

            if submit_novo:
                if not novo_nome.strip() or not senha_acesso:
                    st.error("⚠️ Nome e Senha são obrigatórios para criar o perfil!")
                else:
                    foto_url = ""
                    if foto_upload:
                        ext      = foto_upload.name.split('.')[-1]
                        nome_arq = f"{uuid.uuid4()}.{ext}"
                        supabase.storage.from_("fotos_mural").upload(nome_arq, foto_upload.getvalue())
                        foto_url = supabase.storage.from_("fotos_mural").get_public_url(nome_arq)

                    dados_insert = {
                        "nome":            novo_nome.strip(),
                        "data_nascimento": str(nova_data),
                        "curiosidade":     curiosidade,
                        "senha_perfil":    senha_acesso,
                        "perfil_completo": True,
                        "foto_url":        foto_url,
                    }
                    supabase.table("aniversariantes").insert(dados_insert).execute()
                    st.success(f"✅ Cadastro de **{novo_nome.strip()}** criado com sucesso! Bem-vindo(a) à equipe. 🎉")

    # --- ATUALIZAÇÃO ---
    elif nome_selecionado != "":
        dados_atuais  = next(item for item in lista_funcionarios if item["nome"] == nome_selecionado)
        foi_completado = to_bool(dados_atuais.get("perfil_completo", False))

        with st.form("form_update"):
            st.write(f"### Olá, {nome_selecionado}! 👋")

            if foi_completado:
                st.warning("🔒 Este perfil já foi preenchido. Para editar, insira sua senha de perfil.")
            else:
                st.info("✨ Seu perfil ainda está básico. Vamos completá-lo? Crie uma senha para protegê-lo.")

            senha_acesso  = st.text_input(
                "Senha do seu perfil" if foi_completado else "Crie uma senha para seu perfil",
                type="password"
            )
            curiosidade = st.text_area("Sua curiosidade", max_chars=200)
            foto_upload = st.file_uploader("Sua foto", type=["jpg", "png", "jpeg"])

            submit_update = st.form_submit_button("💾 Salvar Informações")

            if submit_update:
                res_check      = supabase.table("aniversariantes").select("senha_perfil").eq("nome", nome_selecionado).single().execute()
                senha_no_banco = res_check.data.get("senha_perfil") if res_check.data else None

                if foi_completado and senha_acesso != senha_no_banco:
                    st.error("❌ Senha incorreta! Você não tem permissão para alterar este perfil.")
                elif not senha_acesso:
                    st.error("⚠️ Você precisa definir uma senha para seu perfil.")
                else:
                    foto_url = ""
                    if foto_upload:
                        ext      = foto_upload.name.split('.')[-1]
                        nome_arq = f"{uuid.uuid4()}.{ext}"
                        supabase.storage.from_("fotos_mural").upload(nome_arq, foto_upload.getvalue())
                        foto_url = supabase.storage.from_("fotos_mural").get_public_url(nome_arq)

                    dados_update = {
                        "curiosidade":     curiosidade,
                        "senha_perfil":    senha_acesso,
                        "perfil_completo": True,
                    }
                    if foto_url:
                        dados_update["foto_url"] = foto_url

                    supabase.table("aniversariantes").update(dados_update).eq("nome", nome_selecionado).execute()
                    st.success("✅ Perfil atualizado e protegido com sucesso!")

except Exception as e:
    st.error(f"Erro ao carregar dados: {e}")
