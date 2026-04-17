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

# --- 2. UTILITÁRIOS ---
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

exibir_mural    = to_bool(config.get("exibir_mural",    False))
liberar_recados = to_bool(config.get("liberar_recados", False))

# --- 3. ADMIN ---
st.sidebar.title("⚙️ Administração CGC")
senha_digitada = st.sidebar.text_input("Acesso restrito", type="password")
SENHA_CORRETA  = "cgc2026"
modo_admin     = (senha_digitada == SENHA_CORRETA)

if modo_admin:
    st.sidebar.success("Modo Admin Ativado! 🔓")

    def atualizar_config(chave, valor):
        supabase.table("configuracoes_mural") \
            .update({"valor": valor}) \
            .eq("chave", chave) \
            .execute()

    novo_cadastro = st.sidebar.checkbox(
        "Liberar Aba de Cadastro",
        value=to_bool(config.get("liberar_cadastro", True))
    )
    novo_recados = st.sidebar.checkbox(
        "Liberar Aba de Recados",
        value=liberar_recados
    )
    novo_exibir = st.sidebar.checkbox(
        "REVELAR MURAL FINAL",
        value=exibir_mural
    )

    st.sidebar.divider()
    cor_fundo     = st.sidebar.color_picker("Cor base do Mural", config.get("cor_fundo", "#0f172a"))
    imagem_fundo  = st.sidebar.file_uploader("Imagem de Fundo", type=["jpg", "png", "jpeg"])

    # Lê o arquivo UMA ÚNICA VEZ e reutiliza
    img_bytes_admin  = None
    img_b64_admin    = None
    img_tipo_admin   = None
    if imagem_fundo is not None:
        img_bytes_admin = imagem_fundo.read()
        img_b64_admin   = base64.b64encode(img_bytes_admin).decode()
        img_tipo_admin  = imagem_fundo.type

    if st.sidebar.button("💾 Salvar alterações"):
        atualizar_config("liberar_cadastro", novo_cadastro)
        atualizar_config("liberar_recados",  novo_recados)
        atualizar_config("exibir_mural",     novo_exibir)
        atualizar_config("cor_fundo",        cor_fundo)
        if img_b64_admin is not None:
            fundo_data_url = f"data:{img_tipo_admin};base64,{img_b64_admin}"
            atualizar_config("imagem_fundo", fundo_data_url)
        st.sidebar.success("Atualizado!")
        st.rerun()

    # Preview do fundo para o admin
    if img_b64_admin is not None:
        estilo_fundo = (
            f"background-image: url('data:{img_tipo_admin};base64,{img_b64_admin}'); "
            f"background-size: cover; background-position: center; background-attachment: fixed;"
        )
    else:
        estilo_fundo = f"background-color: {cor_fundo};"

elif senha_digitada != "":
    st.sidebar.error("Senha incorreta.")
    imagem_salva = config.get("imagem_fundo", "")
    cor_salva    = config.get("cor_fundo", "#0f172a")
    if imagem_salva:
        estilo_fundo = (
            f"background-image: url('{imagem_salva}'); "
            f"background-size: cover; background-position: center; background-attachment: fixed;"
        )
    else:
        estilo_fundo = f"background-color: {cor_salva};"
else:
    imagem_salva = config.get("imagem_fundo", "")
    cor_salva    = config.get("cor_fundo", "#0f172a")
    if imagem_salva:
        estilo_fundo = (
            f"background-image: url('{imagem_salva}'); "
            f"background-size: cover; background-position: center; background-attachment: fixed;"
        )
    else:
        estilo_fundo = f"background-color: {cor_salva};"

# --- 4. PORTEIRO ---
if not exibir_mural:
    st.markdown("""
    <div style="text-align:center; padding: 80px 20px;">
        <div style="font-size: 5rem;">🎉</div>
        <h1 style="font-size: 2.5rem; margin: 20px 0 10px;">Mural de Aniversariantes</h1>
        <p style="font-size: 1.2rem; color: #94a3b8;">
            O Mural está sendo preparado com carinho! 🤫<br>
            Fique atento às comunicações da CGC para a grande revelação.
        </p>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# --- 5. DADOS ---
mes_atual = datetime.now().month
meses_ptbr = {
    1: 'Janeiro',  2: 'Fevereiro', 3: 'Março',    4: 'Abril',
    5: 'Maio',     6: 'Junho',     7: 'Julho',     8: 'Agosto',
    9: 'Setembro', 10: 'Outubro',  11: 'Novembro', 12: 'Dezembro'
}
nome_mes_atual = meses_ptbr[mes_atual]

try:
    response     = supabase.table("aniversariantes").select("*").execute()
    dados        = response.data or []
    resp_recados = supabase.table("recados").select("*").execute()
    df_recados   = pd.DataFrame(resp_recados.data) if resp_recados.data else pd.DataFrame()
except Exception as e:
    st.error(f"Erro no banco: {e}")
    dados      = []
    df_recados = pd.DataFrame()

# Paleta de cores para os post-its
POSTIT_COLORS = [
    {"bg": "#fef08a", "text": "#3f6212"},  # Amarelo
    {"bg": "#bbf7d0", "text": "#14532d"},  # Verde
    {"bg": "#fed7aa", "text": "#7c2d12"},  # Laranja
    {"bg": "#fecdd3", "text": "#881337"},  # Rosa
    {"bg": "#bfdbfe", "text": "#1e3a5f"},  # Azul
    {"bg": "#e9d5ff", "text": "#4c1d95"},  # Roxo
]

# --- 6. MURAL ---
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
            <link rel="preconnect" href="https://fonts.googleapis.com">
            <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;900&family=Lato:wght@300;400;700&family=Caveat:wght@500;700&display=swap" rel="stylesheet">
            <style>
                *, *::before, *::after {{
                    margin: 0; padding: 0; box-sizing: border-box;
                }}
                body {{
                    {estilo_fundo}
                    font-family: 'Lato', sans-serif;
                    color: #f8fafc;
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    padding: 40px 20px 60px;
                    min-height: 100vh;
                }}
                /* ── Header ── */
                .mural-header {{
                    text-align: center;
                    margin-bottom: 60px;
                    position: relative;
                }}
                .mural-header .subtitulo {{
                    font-family: 'Lato', sans-serif;
                    font-weight: 300;
                    font-size: 0.95rem;
                    letter-spacing: 5px;
                    text-transform: uppercase;
                    color: #94a3b8;
                    margin-bottom: 10px;
                }}
                .mural-header h1 {{
                    font-family: 'Playfair Display', serif;
                    font-size: 3.2rem;
                    font-weight: 900;
                    color: #ffffff;
                    text-shadow: 0 2px 20px rgba(0,0,0,0.6);
                    line-height: 1.1;
                }}
                .mural-header .mes-destaque {{
                    color: #38bdf8;
                }}
                .header-linha {{
                    width: 80px;
                    height: 3px;
                    background: linear-gradient(90deg, #38bdf8, #818cf8);
                    margin: 16px auto 0;
                    border-radius: 2px;
                }}
                /* ── Grid ── */
                .mural-grid {{
                    display: flex;
                    flex-wrap: wrap;
                    gap: 50px;
                    justify-content: center;
                    max-width: 1300px;
                    width: 100%;
                }}
                /* ── Card de Aniversariante ── */
                .aniversariante-card {{
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    gap: 24px;
                    animation: fadeInUp 0.6s ease both;
                }}
                @keyframes fadeInUp {{
                    from {{ opacity: 0; transform: translateY(24px); }}
                    to   {{ opacity: 1; transform: translateY(0); }}
                }}
                /* ── Polaroid ── */
                .polaroid {{
                    background: #fffef5;
                    padding: 14px 14px 40px;
                    border-radius: 3px;
                    box-shadow:
                        0 4px 6px rgba(0,0,0,0.2),
                        0 12px 30px rgba(0,0,0,0.45),
                        inset 0 1px 0 rgba(255,255,255,0.8);
                    width: 240px;
                    color: #1e293b;
                    text-align: center;
                    position: relative;
                    transition: transform 0.3s ease, box-shadow 0.3s ease;
                }}
                .polaroid:hover {{
                    transform: scale(1.04) rotate(-0.5deg);
                    box-shadow:
                        0 8px 16px rgba(0,0,0,0.3),
                        0 24px 50px rgba(0,0,0,0.55);
                }}
                .foto {{
                    width: 100%;
                    height: 210px;
                    background-size: cover;
                    background-position: center top;
                    border-radius: 1px;
                    border: 1px solid #e2e8f0;
                    overflow: hidden;
                }}
                .foto-placeholder {{
                    width: 100%;
                    height: 210px;
                    background: linear-gradient(135deg, #e2e8f0, #cbd5e1);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-size: 4rem;
                    border-radius: 1px;
                }}
                .nome {{
                    font-family: 'Playfair Display', serif;
                    font-size: 1.15rem;
                    font-weight: 700;
                    margin-top: 12px;
                    color: #1e293b;
                    line-height: 1.2;
                }}
                .data-badge {{
                    display: inline-block;
                    background: linear-gradient(135deg, #ef4444, #f97316);
                    color: #fff;
                    font-size: 0.75rem;
                    font-weight: 700;
                    letter-spacing: 1px;
                    text-transform: uppercase;
                    padding: 3px 10px;
                    border-radius: 20px;
                    margin-top: 6px;
                    box-shadow: 0 2px 6px rgba(239,68,68,0.4);
                }}
                .curiosidade {{
                    font-size: 0.78rem;
                    color: #64748b;
                    font-style: italic;
                    margin-top: 6px;
                    padding: 0 4px;
                    line-height: 1.4;
                }}
                /* ── Área de Post-its ── */
                .area-post-it {{
                    border: 2px dashed rgba(255,255,255,0.2);
                    border-radius: 10px;
                    width: 290px;
                    min-height: 170px;
                    padding: 14px;
                    display: flex;
                    flex-wrap: wrap;
                    gap: 12px;
                    justify-content: center;
                    align-content: flex-start;
                    background: rgba(0,0,0,0.15);
                    backdrop-filter: blur(4px);
                }}
                .post-it {{
                    padding: 12px 10px;
                    width: 120px;
                    min-height: 90px;
                    box-shadow:
                        2px 3px 8px rgba(0,0,0,0.35),
                        inset 0 -3px 0 rgba(0,0,0,0.08);
                    font-family: 'Caveat', cursive;
                    font-size: 0.9rem;
                    border-radius: 2px;
                    display: flex;
                    flex-direction: column;
                    justify-content: space-between;
                    gap: 8px;
                    word-break: break-word;
                    transition: transform 0.2s ease;
                    position: relative;
                }}
                .post-it::before {{
                    content: '';
                    position: absolute;
                    top: 0; left: 50%;
                    transform: translateX(-50%);
                    width: 30px; height: 6px;
                    background: rgba(0,0,0,0.12);
                    border-radius: 0 0 3px 3px;
                }}
                .post-it:hover {{
                    transform: scale(1.06) !important;
                    z-index: 10;
                }}
                .post-it-msg {{
                    font-size: 0.92rem;
                    line-height: 1.35;
                    font-weight: 500;
                }}
                .post-it-autor {{
                    font-size: 0.78rem;
                    font-weight: 700;
                    opacity: 0.75;
                    text-align: right;
                    border-top: 1px solid rgba(0,0,0,0.1);
                    padding-top: 5px;
                    margin-top: auto;
                }}
                .sem-recados {{
                    color: rgba(255,255,255,0.4);
                    font-size: 0.82rem;
                    text-align: center;
                    padding: 30px 10px;
                    font-family: 'Lato', sans-serif;
                    font-style: italic;
                    width: 100%;
                }}
                /* ── Emoji de bolo decorativo ── */
                .bolo-emoji {{
                    font-size: 1.5rem;
                    position: absolute;
                    top: -14px;
                    right: -10px;
                    filter: drop-shadow(0 2px 4px rgba(0,0,0,0.4));
                }}
            </style>
        </head>
        <body>
            <div class="mural-header">
                <p class="subtitulo">🎂 Celebrando</p>
                <h1>Aniversariantes de<br><span class="mes-destaque">{nome_mes_atual}</span></h1>
                <div class="header-linha"></div>
            </div>
            <div class="mural-grid">
        """

        cartoes_html = ""

        for idx, (_, row) in enumerate(df_mes.iterrows()):
            nome = str(row.get("nome", "Sem nome"))
            dia  = row['data_nascimento'].day if pd.notna(row['data_nascimento']) else "?"

            img_url = str(row.get("foto_url", "")).strip()
            if img_url:
                foto_html = f'<div class="foto" style="background-image: url(\'{img_url}\');"></div>'
            else:
                foto_html = '<div class="foto-placeholder">👤</div>'

            texto_curiosidade = str(row.get("curiosidade", "")).strip()
            curiosidade_html = ""
            if texto_curiosidade:
                curiosidade_html = f'<div class="curiosidade">✨ {texto_curiosidade}</div>'

            # ── Post-its ──
            post_its_html = ""
            if not df_recados.empty and 'para_quem' in df_recados.columns:
                recados_pessoa = df_recados[df_recados['para_quem'] == nome]
                if recados_pessoa.empty:
                    post_its_html = '<p class="sem-recados">📌 Aguardando recados...</p>'
                else:
                    for i, (_, recado) in enumerate(recados_pessoa.iterrows()):
                        mensagem = str(recado.get("mensagem", "")).strip()
                        autor    = str(recado.get("de_quem", "Anônimo")).strip()
                        rotacao  = random.randint(-6, 6)
                        cor      = POSTIT_COLORS[i % len(POSTIT_COLORS)]
                        post_its_html += f"""
                        <div class="post-it"
                             style="background:{cor['bg']}; color:{cor['text']}; transform: rotate({rotacao}deg);">
                            <div class="post-it-msg">{mensagem}</div>
                            <div class="post-it-autor">✏️ {autor}</div>
                        </div>
                        """
            else:
                post_its_html = '<p class="sem-recados">📌 Aguardando recados...</p>'

            delay = idx * 0.12

            cartoes_html += f"""
            <div class="aniversariante-card" style="animation-delay: {delay}s;">
                <div class="polaroid">
                    <span class="bolo-emoji">🎂</span>
                    {foto_html}
                    <div class="nome">{nome}</div>
                    <div class="data-badge">🎉 {dia} de {nome_mes_atual}</div>
                    {curiosidade_html}
                </div>
                <div class="area-post-it">{post_its_html}</div>
            </div>
            """

        full_html = html_base + cartoes_html + "</div></body></html>"
        components.html(full_html, height=1600, scrolling=True)

    else:
        st.info(f"🗓️ Nenhum aniversariante cadastrado para {nome_mes_atual}.")
else:
    st.warning("⚠️ Nenhum dado encontrado no banco de dados.")
