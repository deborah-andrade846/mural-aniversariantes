import streamlit as st
from supabase import create_client, Client
import datetime
import pandas as pd
from utils import get_supabase, to_bool, carregar_config

st.set_page_config(page_title="Deixe um Recado", page_icon="💌")

supabase = get_supabase()

# --- CONTROLE DE ACESSO ---
config = carregar_config()
if not to_bool(config.get("liberar_recados", False)):
    st.warning("### 📮 A caixinha de recados abrirá em breve!\n\nAguarde o momento da festa para enviar sua mensagem.")
    st.stop()

# --- UI ---
st.title("💌 Mural de Recados")
st.write("Escreva uma mensagem para os aniversariantes do mês. Ela vai virar um Post-it digital no quadro!")

mes_atual = datetime.datetime.now().month

try:
    with st.spinner("Carregando aniversariantes do mês..."):
        resp_aniv = supabase.table("aniversariantes").select("*").execute()
    df_aniv = pd.DataFrame(resp_aniv.data) if resp_aniv.data else pd.DataFrame()

except Exception:
    st.error("Não foi possível conectar ao banco de dados. Tente novamente em instantes.")
    st.stop()

if df_aniv.empty:
    st.info("📭 O banco de dados de aniversariantes está vazio.")
    st.stop()

df_aniv['data_nascimento'] = pd.to_datetime(df_aniv['data_nascimento'], errors='coerce')
df_mes = df_aniv[df_aniv['data_nascimento'].dt.month == mes_atual]

if df_mes.empty:
    st.info("📅 Nenhum aniversariante cadastrado para este mês ainda.")
    st.stop()

# Ordena alfabeticamente para facilitar a busca
nomes = sorted(df_mes['nome'].tolist())

with st.form("form_recado", clear_on_submit=True):
    para_quem = st.selectbox("🎂 Para quem é o recado?", nomes)
    de_quem = st.text_input("✏️ Seu Nome (quem está enviando)")
    mensagem = st.text_area(
        "💬 Sua Mensagem",
        max_chars=150,
        placeholder="Escreva uma mensagem especial... (máx. 150 caracteres)"
    )

    # Contador de caracteres visual
    if mensagem:
        st.caption(f"{len(mensagem)}/150 caracteres")

    col1, col2 = st.columns([3, 1])
    with col2:
        submit = st.form_submit_button("📌 Colar Post-it", use_container_width=True)

    if submit:
        if not de_quem.strip():
            st.error("⚠️ Preencha seu nome antes de enviar!")
        elif not mensagem.strip():
            st.error("⚠️ Escreva uma mensagem antes de enviar!")
        else:
            try:
                novo_recado = {
                    "para_quem": para_quem,
                    "de_quem":   de_quem.strip(),
                    "mensagem":  mensagem.strip(),
                }
                supabase.table("recados").insert(novo_recado).execute()
                st.success(f"✅ Post-it colado com sucesso para **{para_quem}**! Vá na aba do Mural para ver. 🎉")
            except Exception:
                st.error("Erro ao enviar o recado. Tente novamente.")
