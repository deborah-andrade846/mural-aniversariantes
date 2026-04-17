import streamlit as st
from supabase import create_client, Client
import datetime
import pandas as pd

st.set_page_config(page_title="Deixe um Recado", page_icon="💌")

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
if not to_bool(config.get("liberar_recados", False)):
    st.warning("### 📮 A caixinha de recados abrirá em breve!\n\nAguarde o momento da festa para enviar sua mensagem.")
    st.stop()

# --- UI ---
st.title("💌 Mural de Recados")
st.write("Escreva uma mensagem para os aniversariantes do mês. Ela vai virar um Post-it digital no quadro!")

# --- DADOS ---
mes_atual = datetime.datetime.now().month

try:
    resp_aniv = supabase.table("aniversariantes").select("*").execute()
    df_aniv   = pd.DataFrame(resp_aniv.data) if resp_aniv.data else pd.DataFrame()

    if not df_aniv.empty:
        df_aniv['data_nascimento'] = pd.to_datetime(df_aniv['data_nascimento'], errors='coerce')
        df_mes = df_aniv[df_aniv['data_nascimento'].dt.month == mes_atual]

        if not df_mes.empty:
            nomes = df_mes['nome'].tolist()

            with st.form("form_recado", clear_on_submit=True):
                para_quem = st.selectbox("🎂 Para quem é o recado?", nomes)
                de_quem   = st.text_input("✏️ Seu Nome (quem está enviando)")
                mensagem  = st.text_area(
                    "💬 Sua Mensagem",
                    max_chars=150,
                    placeholder="Escreva uma mensagem especial... (máx. 150 caracteres)"
                )

                col1, col2 = st.columns([3, 1])
                with col2:
                    submit = st.form_submit_button("📌 Colar Post-it", use_container_width=True)

                if submit:
                    if de_quem.strip() and mensagem.strip():
                        novo_recado = {
                            "para_quem": para_quem,
                            "de_quem":   de_quem.strip(),
                            "mensagem":  mensagem.strip(),
                        }
                        supabase.table("recados").insert(novo_recado).execute()
                        st.success(f"✅ Post-it colado com sucesso para **{para_quem}**! Vá na aba do Mural para ver. 🎉")
                    else:
                        st.error("⚠️ Preencha seu nome e a mensagem antes de enviar!")
        else:
            st.info("📅 Nenhum aniversariante cadastrado para este mês ainda.")
    else:
        st.info("📭 O banco de dados de aniversariantes está vazio.")

except Exception as e:
    st.error(f"Erro ao conectar: {e}")
