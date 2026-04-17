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

# --- MURAL DIRETO (SEM ABA) ---
if dados:
    df = pd.DataFrame(dados)
    df['data_nascimento'] = pd.to_datetime(df['data_nascimento'], errors='coerce')
    df_mes = df[df['data_nascimento'].dt.month == mes_atual].copy()

    if not df_mes.empty:
        df_mes = df_mes.sort_values(by='data_nascimento')
            html_base = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <style>
                    * {{ margin: 0; padding: 0; box-sizing: border-box; font-family: 'Segoe UI', sans-serif; }}
                    body {{ {estilo_fundo} color: #f8fafc; display: flex; flex-direction: column; align-items: center; padding: 30px 20px; min-height: 100vh; }}
                    .mural-header {{ text-align: center; margin-bottom: 50px; }}
                    .mural-header h1 {{ font-size: 3rem; text-transform: uppercase; letter-spacing: 3px; color: #ffffff; text-shadow: 2px 2px 8px rgba(0,0,0,0.8); border-bottom: 2px solid #38bdf8; padding-bottom: 10px; display: inline-block; }}
                    .mural-grid {{ display: flex; flex-wrap: wrap; gap: 40px; justify-content: center; max-width: 1200px; }}
                    .aniversariante-card {{ display: flex; flex-direction: column; align-items: center; gap: 20px; }}
                    .polaroid {{ background-color: #ffffff; padding: 15px 15px 30px 15px; border-radius: 4px; box-shadow: 0 10px 25px rgba(0,0,0,0.5); width: 250px; color: #1e293b; text-align: center; }}
                    .foto {{ width: 100%; height: 220px; background-size: cover; background-position: center; border-radius: 2px; border: 1px solid #cbd5e1; }}
                    .nome {{ font-size: 1.5rem; font-weight: bold; margin-top: 10px; color: #1e293b; }}
                    .data {{ font-size: 1rem; color: #ef4444; font-weight: bold; }}
                    .area-post-it {{ border: 2px dashed rgba(255,255,255,0.3); border-radius: 8px; width: 300px; min-height: 180px; padding: 10px; display: flex; flex-wrap: wrap; gap: 10px; justify-content: center; background-color: rgba(0,0,0,0.1); }}
                    .post-it {{ background-color: #fef08a; color: #3f6212; padding: 12px; width: 130px; box-shadow: 2px 4px 6px rgba(0,0,0,0.3); font-family: 'Comic Sans MS', cursive; font-size: 0.85rem; border-radius: 2px; }}
                </style>
            </head>
            <body>
                <div class="mural-header"><h1>Aniversariantes de {nome_mes_atual}</h1></div>
                <div class="mural-grid">
            """

            cartoes_html = ""

            for _, row in df_mes.iterrows():

                nome = str(row.get("nome", "Sem nome"))
                dia = row['data_nascimento'].day if pd.notna(row['data_nascimento']) else ""

                img_url = str(row.get("foto_url", "")).strip()
                if img_url:
                    img_style = f"background-image: url('{img_url}');"
                else:
                    img_style = "background-color: #e2e8f0;"

                curiosidade = ""
                if pd.notna(row.get("curiosidade")):
                    curiosidade = f"<div style='font-size: 0.8rem; color: #64748b; margin-top:5px;'><i>{row['curiosidade']}</i></div>"

                post_its_html = ""

                if not df_recados.empty and liberar_recados:
                    recados_pessoa = df_recados[df_recados['para_quem'] == nome]

                    if recados_pessoa.empty:
                        post_its_html = "<p style='color: rgba(255,255,255,0.5); font-size: 0.8rem; margin-top: 60px;'>Aguardando recados... 📌</p>"
                    else:
                        for _, recado in recados_pessoa.iterrows():
                            mensagem = str(recado.get("mensagem", ""))
                            autor = str(recado.get("de_quem", ""))
                            rotacao = random.randint(-7, 7)

                            post_its_html += f"""
                            <div class="post-it" style="transform: rotate({rotacao}deg);">
                                <strong>"{mensagem}"</strong><br><br>
                                <small>✏️ {autor}</small>
                            </div>
                            """
                else:
                    post_its_html = "<p style='color: rgba(255,255,255,0.5); font-size: 0.8rem; margin-top: 60px;'>Aguardando recados... 📌</p>"

                cartoes_html += f"""
                <div class="aniversariante-card">
                    <div class="polaroid">
                        <div class="foto" style="{img_style}"></div>
                        <div class="nome">{nome}</div>
                        <div class="data">{dia} de {nome_mes_atual}</div>
                        {curiosidade}
                    </div>
                    <div class="area-post-it">{post_its_html}</div>
                </div>
                """

            full_html = html_base + cartoes_html + "</div></body></html>"

            components.html(full_html, height=1500, scrolling=True)

        else:
            st.info(f"Nenhum aniversariante em {nome_mes_atual}.")
    else:
        st.warning("Nenhum dado encontrado no banco.")
