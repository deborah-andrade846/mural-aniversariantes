import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
from datetime import datetime
from supabase import create_client, Client
import random
import base64

st.set_page_config(page_title="Mural de Clima", layout="wide", page_icon="🎉")

# --- 1. CONEXÃO ---
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

# --- 2. CONFIG ---
def carregar_config():
    try:
        resp = supabase.table("configuracoes_mural").select("*").execute()
        return {item['chave']: item['valor'] for item in resp.data}
    except:
        return {}

config = carregar_config()

exibir_mural = config.get("exibir_mural", False)
liberar_recados = config.get("liberar_recados", False)

# --- 3. ADMIN ---
st.sidebar.title("⚙️ Administração CGC")
senha_digitada = st.sidebar.text_input("Acesso restrito", type="password")
SENHA_CORRETA = "cgc2026"

modo_admin = senha_digitada == SENHA_CORRETA

if modo_admin:
    st.sidebar.success("Modo Admin Ativado! 🔓")

    def atualizar_config(chave, valor):
        supabase.table("configuracoes_mural")\
            .update({"valor": valor})\
            .eq("chave", chave)\
            .execute()

    novo_cadastro = st.sidebar.checkbox("Liberar Aba de Cadastro", value=config.get("liberar_cadastro", True))
    novo_recados = st.sidebar.checkbox("Liberar Aba de Recados", value=liberar_recados)
    novo_exibir = st.sidebar.checkbox("REVELAR MURAL FINAL", value=exibir_mural)

    if st.sidebar.button("💾 Salvar alterações"):
        atualizar_config("liberar_cadastro", novo_cadastro)
        atualizar_config("liberar_recados", novo_recados)
        atualizar_config("exibir_mural", novo_exibir)
        st.sidebar.success("Atualizado!")
        st.rerun()

    st.sidebar.divider()
    cor_fundo = st.sidebar.color_picker("Cor base do Mural", "#0f172a")
    imagem_fundo = st.sidebar.file_uploader("Imagem de Fundo", type=["jpg", "png", "jpeg"])

    if imagem_fundo is not None:
        base64_img = base64.b64encode(imagem_fundo.read()).decode()
        tipo_img = imagem_fundo.type
        estilo_fundo = f"background-image: url('data:{tipo_img};base64,{base64_img}'); background-size: cover; background-position: center; background-attachment: fixed;"
    else:
        estilo_fundo = f"background-color: {cor_fundo};"
else:
    if senha_digitada != "":
        st.sidebar.error("Senha incorreta.")
    estilo_fundo = "background-color: #0f172a;"

# --- 4. PORTEIRO DO MURAL ---
if not exibir_mural:
    st.title("🎉 Mural de Aniversariantes")
    st.info("### O Mural está sendo preparado com carinho! 🤫\n\nFique atento às comunicações da CGC para a grande revelação em breve.")
    st.stop()

# --- 5. DADOS ---
mes_atual = datetime.now().month
meses_ptbr = {1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril', 5: 'Maio', 6: 'Junho', 
              7: 'Julho', 8: 'Agosto', 9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'}
nome_mes_atual = meses_ptbr[mes_atual]

try:
    response = supabase.table("aniversariantes").select("*").execute()
    dados = response.data
    resp_recados = supabase.table("recados").select("*").execute()
    df_recados = pd.DataFrame(resp_recados.data)
except Exception as e:
    st.error(f"Erro no banco: {e}")
    dados = []

# --- 6. MURAL (INALTERADO) ---
if dados:
    df = pd.DataFrame(dados)
    df['data_nascimento'] = pd.to_datetime(df['data_nascimento'])
    df_mes = df[df['data_nascimento'].dt.month == mes_atual].copy()
    
    if not df_mes.empty:
        df_mes = df_mes.sort_values(by='data_nascimento')
        
        html_base = f""" ... """  # (SEU HTML INTACTO)

        cartoes_html = ""
        for index, row in df_mes.iterrows():
            img_style = f"background-image: url('{row['foto_url']}');" if pd.notna(row['foto_url']) and str(row['foto_url']).strip() != "" else "background-color: #e2e8f0;"
            
            curiosidade = f"<div style='font-size: 0.8rem; color: #64748b; margin-top:5px;'><i>{row['curiosidade']}</i></div>" if 'curiosidade' in row and pd.notna(row['curiosidade']) else ""

            post_its_html = ""
            if not df_recados.empty and liberar_recados:
                recados_pessoa = df_recados[df_recados['para_quem'] == row['nome']]
                for _, recado in recados_pessoa.iterrows():
                    rotacao = random.randint(-7, 7)
                    post_its_html += f"""
                    <div class="post-it" style="transform: rotate({rotacao}deg);">
                        <strong>"{recado['mensagem']}"</strong><br><br>
                        <small>✏️ {recado['de_quem']}</small>
                    </div>
                    """

            cartoes_html += f""" ... """

        full_html = html_base + cartoes_html + "</div></body></html>"
        components.html(full_html, height=1500, scrolling=True)
