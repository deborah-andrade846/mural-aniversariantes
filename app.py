import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
from datetime import datetime
from supabase import create_client, Client
import random
import base64

st.set_page_config(page_title="Mural de Clima", layout="wide", page_icon="🎉")

# --- 1. CONTROLE DE VISIBILIDADE (Session State do Código 2) ---
if 'exibir_mural' not in st.session_state:
    st.session_state['exibir_mural'] = False
if 'liberar_recados' not in st.session_state:
    st.session_state['liberar_recados'] = False
if 'liberar_cadastro' not in st.session_state:
    st.session_state['liberar_cadastro'] = True 

# --- 2. PAINEL ADMINISTRATIVO (Segurança do Código 2) ---
st.sidebar.title("⚙️ Administração CGC")
senha_digitada = st.sidebar.text_input("Acesso restrito", type="password")
SENHA_CORRETA = "cgc2026"

if senha_digitada == SENHA_CORRETA:
    st.sidebar.success("Modo Admin Ativado! 🔓")
    st.sidebar.subheader("👁️ Controle de Visibilidade")
    st.session_state['liberar_cadastro'] = st.sidebar.checkbox("Liberar Aba de Cadastro", value=st.session_state['liberar_cadastro'])
    st.session_state['liberar_recados'] = st.sidebar.checkbox("Liberar Aba de Recados", value=st.session_state['liberar_recados'])
    st.session_state['exibir_mural'] = st.sidebar.checkbox("REVELAR MURAL FINAL", value=st.session_state['exibir_mural'])

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

# --- 3. LÓGICA PORTEIRO (Segurança do Código 2) ---
if not st.session_state['exibir_mural'] and senha_digitada != SENHA_CORRETA:
    st.title("🎉 Mural de Aniversariantes")
    st.info("### O Mural está sendo preparado com carinho! 🤫\n\nFique atento às comunicações da CGC para a grande revelação.")
    st.stop()

# --- 4. CONEXÃO E DADOS ---
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

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

# --- 5. MONTAGEM DO VISUAL (Estética do Código 1) ---
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
        for index, row in df_mes.iterrows():
            # Imagem de fundo da foto
            img_style = f"background-image: url('{row['foto_url']}');" if pd.notna(row['foto_url']) and str(row['foto_url']).strip() != "" else "background-color: #e2e8f0;"
            
            # Curiosidade (do código 1)
            curiosidade = f"<div style='font-size: 0.8rem; color: #64748b; margin-top:5px;'><i>{row['curiosidade']}</i></div>" if 'curiosidade' in row and pd.notna(row['curiosidade']) else ""

            # Lógica dos Post-its despojados
            post_its_html = ""
            if not df_recados.empty:
                recados_pessoa = df_recados[df_recados['para_quem'] == row['nome']]
                if recados_pessoa.empty:
                    post_its_html = "<p style='color: rgba(255,255,255,0.5); font-size: 0.8rem; margin-top: 60px;'>Aguardando recados... 📌</p>"
                else:
                    for _, recado in recados_pessoa.iterrows():
                        rotacao = random.randint(-7, 7)
                        post_its_html += f"""
                        <div class="post-it" style="transform: rotate({rotacao}deg);">
                            <strong>"{recado['mensagem']}"</strong><br><br>
                            <small>✏️ {recado['de_quem']}</small>
                        </div>
                        """
            else:
                post_its_html = "<p style='color: rgba(255,255,255,0.5); font-size: 0.8rem; margin-top: 60px;'>Aguardando recados... 📌</p>"

            cartoes_html += f"""
                <div class="aniversariante-card">
                    <div class="polaroid">
                        <div class="foto" style="{img_style}"></div>
                        <div class="nome">{row['nome']}</div>
                        <div class="data">{row['data_nascimento'].day} de {nome_mes_atual}</div>
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
