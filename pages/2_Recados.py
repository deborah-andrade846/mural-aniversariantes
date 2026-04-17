import streamlit as st
from supabase import create_client, Client
import datetime
import pandas as pd
if not st.session_state.get('liberar_recados', False):
    st.warning("### A caixinha de recados abrirá em breve! Aguarde o momento da festa.")
    st.stop()
st.set_page_config(page_title="Deixe um Recado", page_icon="💌")

# Conexão com o banco
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

st.title("💌 Murais de Recados")
st.write("Escreva uma mensagem para os aniversariantes do mês. Ela vai virar um Post-it digital no quadro!")

# 1. Puxar quem faz aniversário neste mês para criar a lista de opções
mes_atual = datetime.datetime.now().month

try:
    resp_aniv = supabase.table("aniversariantes").select("*").execute()
    df_aniv = pd.DataFrame(resp_aniv.data)
    
    if not df_aniv.empty:
        df_aniv['data_nascimento'] = pd.to_datetime(df_aniv['data_nascimento'])
        df_mes = df_aniv[df_aniv['data_nascimento'].dt.month == mes_atual]
        
        if not df_mes.empty:
            # Pega só os nomes para o menu suspenso
            nomes = df_mes['nome'].tolist()
            
            with st.form("form_recado", clear_on_submit=True):
                para_quem = st.selectbox("Para quem é o recado?", nomes)
                de_quem = st.text_input("Seu Nome (Quem está enviando)")
                mensagem = st.text_area("Sua Mensagem (Máximo 150 caracteres)", max_chars=150)
                
                submit = st.form_submit_button("Colar Post-it")
                
                if submit:
                    if de_quem and mensagem:
                        novo_recado = {
                            "para_quem": para_quem,
                            "de_quem": de_quem,
                            "mensagem": mensagem
                        }
                        supabase.table("recados").insert(novo_recado).execute()
                        st.success("✅ Post-it colado com sucesso! Vá na aba do Mural para ver.")
                    else:
                        st.error("Preencha seu nome e a mensagem!")
        else:
            st.info("Nenhum aniversariante cadastrado para este mês ainda.")
    else:
        st.info("O banco de dados de aniversariantes está vazio.")
except Exception as e:
    st.error(f"Erro ao conectar: {e}")
