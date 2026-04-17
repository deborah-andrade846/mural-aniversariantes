import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
from datetime import datetime
from supabase import create_client, Client
import random
import base64

st.set_page_config(page_title="Mural de Clima", layout="wide", page_icon="🎉")

# --- 1. CONEXÃO SUPABASE ---
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

# --- 2. BUSCAR CONFIGURAÇÕES GLOBAIS ---
def carregar_config():
    try:
        config_resp = supabase.table("configuracoes_mural").select("*").execute()
        return {item['chave']: item['valor'] for item in config_resp.data}
    except:
        return {}

config = carregar_config()

exibir_mural = config.get("exibir_mural", False)
liberar_recados = config.get("liberar_recados", False)
liberar_cadastro = config.get("liberar_cadastro", True)

# --- 3. ADMIN ---
st.sidebar.title("⚙️ Administração CGC")
senha_digitada = st.sidebar.text_input("Acesso restrito", type="password")
SENHA_CORRETA = "cgc2026"

modo_admin = senha_digitada == SENHA_CORRETA

if modo_admin:
    st.sidebar.success("Modo Admin Ativado! 🔓")

    st.sidebar.subheader("👁️ Controle Global")

    novo_exibir = st.sidebar.checkbox("REVELAR MURAL FINAL", value=exibir_mural)
    novo_recados = st.sidebar.checkbox("Liberar Recados", value=liberar_recados)
    novo_cadastro = st.sidebar.checkbox("Liberar Cadastro", value=liberar_cadastro)

    def atualizar_config(chave, valor):
        supabase.table("configuracoes_mural")\
            .update({"valor": valor})\
            .eq("chave", chave)\
            .execute()

    if novo_exibir != exibir_mural:
        atualizar_config("exibir_mural", novo_exibir)

    if novo_recados != liberar_recados:
        atualizar_config("liberar_recados", novo_recados)

    if novo_cadastro != liberar_cadastro:
        atualizar_config("liberar_cadastro", novo_cadastro)

    st.sidebar.divider()
    cor_fundo = st.sidebar.color_picker("Cor base do Mural", "#0f172a")
    imagem_fundo = st.sidebar.file_uploader("Imagem de Fundo", type=["jpg", "png", "jpeg"])

    if imagem_fundo is not None:
        base64_img = base64.b64encode(imagem_fundo.read()).decode()
        tipo_img = imagem_fundo.type
        estilo_fundo = f"""
        background-image: url('data:{tipo_img};base64,{base64_img}');
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
        """
    else:
        estilo_fundo = f"background-color: {cor_fundo};"

else:
    if senha_digitada != "":
        st.sidebar.error("Senha incorreta.")
    estilo_fundo = "background-color: #0f172a;"

# --- 4. PORTEIRO (AGORA CORRETO GLOBAL) ---
if not exibir_mural and not modo_admin:
    st.title("🎉 Mural de Aniversariantes")
    st.info("### O Mural está sendo preparado com carinho! 🤫\n\nFique atento às comunicações da CGC para a grande revelação.")
    st.stop()

# --- 5. DADOS ---
mes_atual = datetime.now().month
meses_ptbr = {
    1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril',
    5: 'Maio', 6: 'Junho', 7: 'Julho', 8: 'Agosto',
    9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'
}
nome_mes_atual = meses_ptbr[mes_atual]

try:
    response = supabase.table("aniversariantes").select("*").execute()
    dados = response.data

    resp_recados = supabase.table("recados").select("*").execute()
    df_recados = pd.DataFrame(resp_recados.data)

except Exception as e:
    st.error(f"Erro no banco: {e}")
    dados = []

# --- 6. MONTAGEM ---
if dados:
    df = pd.DataFrame(dados)
    df['data_nascimento'] = pd.to_datetime(df['data_nascimento'])
    df_mes = df[df['data_nascimento'].dt.month == mes_atual].copy()

    if not df_mes.empty:
        df_mes = df_mes.sort_values(by='data_nascimento')

        html_base = f"""
        <!DOCTYPE html>
        <html>
        <head>
        <style>
        * {{ margin:0; padding:0; box-sizing:border-box; font-family:'Segoe UI'; }}
        body {{ {estilo_fundo} color:#f8fafc; display:flex; flex-direction:column; align-items:center; padding:30px; }}
        .grid {{ display:flex; flex-wrap:wrap; gap:40px; justify-content:center; }}
        .card {{ text-align:center; }}
        .polaroid {{ background:#fff; padding:15px; width:250px; }}
        .foto {{ width:100%; height:220px; background-size:cover; }}
        .post {{ background:#fef08a; padding:10px; margin:5px; }}
        </style>
        </head>
        <body>
        <h1>Aniversariantes de {nome_mes_atual}</h1>
        <div class="grid">
        """

        cartoes_html = ""

        for _, row in df_mes.iterrows():

            img_style = f"background-image:url('{row['foto_url']}')" if row.get('foto_url') else ""

            post_its_html = ""

            if not df_recados.empty and liberar_recados:
                recados_pessoa = df_recados[df_recados['para_quem'] == row['nome']]

                for _, recado in recados_pessoa.iterrows():
                    rotacao = random.randint(-7, 7)
                    post_its_html += f"""
                    <div class="post" style="transform:rotate({rotacao}deg)">
                        "{recado['mensagem']}"<br>
                        <small>{recado['de_quem']}</small>
                    </div>
                    """

            cartoes_html += f"""
            <div class="card">
                <div class="polaroid">
                    <div class="foto" style="{img_style}"></div>
                    <h3>{row['nome']}</h3>
                    <p>{row['data_nascimento'].day} de {nome_mes_atual}</p>
                </div>
                <div>{post_its_html}</div>
            </div>
            """

        html_final = html_base + cartoes_html + "</div></body></html>"

        components.html(html_final, height=1500, scrolling=True)

    else:
        st.info(f"Nenhum aniversariante em {nome_mes_atual}.")
else:
    st.warning("Nenhum dado encontrado.")
