import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
from datetime import datetime
import random
import base64
from utils import get_supabase, to_bool, cor_hex_valida, carregar_config

st.set_page_config(page_title="Mural de Aniversariantes", layout="wide", page_icon="🎉")

# --- MODO TV (TELA LIMPA) ---
is_tv = st.query_params.get("tv") == "true"

if is_tv:
    st.markdown("""
        <style>
            header {visibility: hidden;}
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            [data-testid="collapsedControl"] {display: none;}
            .block-container {
                padding-top: 0rem !important;
                padding-bottom: 0rem !important;
                max-width: 100% !important;
            }
        </style>
    """, unsafe_allow_html=True)

# --- 1. CONEXÃO ---
supabase = get_supabase()

config = carregar_config()

exibir_mural    = to_bool(config.get("exibir_mural",    False))
liberar_recados = to_bool(config.get("liberar_recados", False))
liberar_cadastro = to_bool(config.get("liberar_cadastro", True))

# --- 3. ADMIN ---
st.sidebar.title("⚙️ Administração")
senha_digitada = st.sidebar.text_input("Acesso restrito", type="password")
SENHA_CORRETA  = "cgc2026"
modo_admin     = (senha_digitada == SENHA_CORRETA)

if modo_admin:
    st.sidebar.success("Modo Admin Ativado! 🔓")

    def atualizar_config(chave, valor):
        try:
            valor_str = str(valor)
            busca = supabase.table("configuracoes_mural").select("id").eq("chave", chave).execute()
            
            if busca.data and len(busca.data) > 0:
                supabase.table("configuracoes_mural").update({"valor": valor_str}).eq("chave", chave).execute()
            else:
                supabase.table("configuracoes_mural").insert({"chave": chave, "valor": valor_str}).execute()
                    
        except Exception as e:
            st.error(f"Erro ao guardar configuração: {e}")
            raise e

    config = carregar_config()
    exibir_mural = to_bool(config.get("exibir_mural", False))
    liberar_recados = to_bool(config.get("liberar_recados", False))
    liberar_cadastro = to_bool(config.get("liberar_cadastro", True))

    st.sidebar.divider()
    
    with st.sidebar.expander("🔐 Controlos de Acesso", expanded=True):
        novo_cadastro = st.checkbox("Libertar Aba de Cadastro", value=liberar_cadastro)
        novo_recados = st.checkbox("Libertar Aba de Recados", value=liberar_recados)
        novo_exibir = st.checkbox("🎉 REVELAR MURAL FINAL", value=exibir_mural)

    with st.sidebar.expander("🎨 Personalização Visual", expanded=False):
        cor_fundo_banco = config.get("cor_fundo")
        if cor_hex_valida(cor_fundo_banco):
            cor_fundo = st.color_picker("Cor base do Mural", value=cor_fundo_banco)
        else:
            cor_fundo = st.color_picker("Cor base do Mural")
            
        imagem_fundo  = st.file_uploader("Imagem de Fundo", type=["jpg", "png", "jpeg"])

    img_bytes_admin  = None
    img_b64_admin    = None
    img_tipo_admin   = None
    if imagem_fundo is not None:
        img_bytes_admin = imagem_fundo.read()
        img_b64_admin   = base64.b64encode(img_bytes_admin).decode()
        img_tipo_admin  = imagem_fundo.type

    st.sidebar.write("") 
    if st.sidebar.button("💾 Guardar alterações", type="primary", use_container_width=True):
        atualizar_config("liberar_cadastro", novo_cadastro)
        atualizar_config("liberar_recados",  novo_recados)
        atualizar_config("exibir_mural",     novo_exibir)
        atualizar_config("cor_fundo",        cor_fundo)
        if img_b64_admin is not None:
            fundo_data_url = f"data:{img_tipo_admin};base64,{img_b64_admin}"
            atualizar_config("imagem_fundo", fundo_data_url)
        config = carregar_config()
        st.sidebar.success("Atualizado!")
        st.rerun()

    if img_b64_admin is not None:
        estilo_fundo = (
            f"background-image: url('data:{img_tipo_admin};base64,{img_b64_admin}'); "
            f"background-size: cover; background-position: center top; background-repeat: no-repeat;"
        )
    else:
        estilo_fundo = f"background-color: {cor_fundo};"

elif senha_digitada != "":
    st.sidebar.error("Senha incorreta.")
    imagem_salva = config.get("imagem_fundo", "")
    cor_salva    = config.get("cor_fundo")
    if imagem_salva:
        estilo_fundo = (
            f"background-image: url('{imagem_salva}'); "
            f"background-size: cover; background-position: center top; background-repeat: no-repeat;"
        )
    elif cor_hex_valida(cor_salva):
        estilo_fundo = f"background-color: {cor_salva};"
    else:
        estilo_fundo = ""
else:
    imagem_salva = config.get("imagem_fundo", "")
    cor_salva    = config.get("cor_fundo")
    if imagem_salva:
        estilo_fundo = (
            f"background-image: url('{imagem_salva}'); "
            f"background-size: cover; background-position: center top; background-repeat: no-repeat;"
        )
    elif cor_hex_valida(cor_salva):
        estilo_fundo = f"background-color: {cor_salva};"
    else:
        estilo_fundo = ""

# --- 4. PORTEIRO ---
if not exibir_mural:
    st.markdown(f"""
    <style>
        .stApp {{
            min-height: 100vh;
            {estilo_fundo}
            background-attachment: scroll !important;
            background-size: cover !important;
            background-position: center top !important;
            background-repeat: no-repeat !important;
        }}
        .porteiro-card {{
            background: rgba(0, 0, 0, 0.50);
            backdrop-filter: blur(14px);
            -webkit-backdrop-filter: blur(14px);
            border: 1px solid rgba(255, 255, 255, 0.15);
            border-radius: 20px;
            padding: clamp(30px, 5vw, 60px) clamp(20px, 4vw, 50px);
            text-align: center;
            width: min(90vw, 560px);
            margin: clamp(6vh, 10vh, 15vh) auto;
            box-shadow: 0 8px 40px 0 rgba(0, 0, 0, 0.5);
            color: white;
            animation: fadeIn 1s ease-in-out;
        }}
        .emoji-animado {{ font-size: 5rem; display: inline-block; animation: pulse 2s infinite; margin-bottom: 10px; filter: drop-shadow(0 4px 6px rgba(0,0,0,0.3)); }}
        .porteiro-titulo {{ font-family: 'Playfair Display', serif; font-size: 2.5rem; font-weight: 700; margin-bottom: 15px; text-shadow: 0 2px 8px rgba(0,0,0,0.7); }}
        .porteiro-texto {{ font-family: 'Lato', sans-serif; font-size: 1.1rem; line-height: 1.6; color: #e2e8f0; text-shadow: 0 1px 4px rgba(0,0,0,0.7); }}
        @keyframes pulse {{ 0% {{ transform: scale(1); }} 50% {{ transform: scale(1.15) rotate(-5deg); }} 100% {{ transform: scale(1); }} }}
        @keyframes fadeIn {{ from {{ opacity: 0; transform: translateY(20px); }} to {{ opacity: 1; transform: translateY(0); }} }}
    </style>
    <div class="porteiro-card">
        <div class="emoji-animado">🤫</div>
        <div class="porteiro-titulo">Mural em Preparação</div>
        <div class="porteiro-texto">
            A equipa está a tratar de cada detalhe com muito carinho!<br><br>
            Fique atento às comunicações da GAFI para a grande revelação do nosso quadro de aniversariantes.
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# --- 5. DADOS ---
mes_atual = datetime.now().month
meses_ptbr = {
    1: 'Janeiro',  2: 'Fevereiro', 3: 'Março',    4: 'Abril',
    5: 'Maio',     6: 'Junho',     7: 'Julho',    8: 'Agosto',
    9: 'Setembro', 10: 'Outubro',  11: 'Novembro', 12: 'Dezembro'
}
nome_mes_atual = meses_ptbr[mes_atual]

try:
    with st.spinner("A carregar mural..."):
        response     = supabase.table("aniversariantes").select("*").execute()
        dados        = response.data or []
        resp_recados = supabase.table("recados").select("*").execute()
        df_recados   = pd.DataFrame(resp_recados.data) if resp_recados.data else pd.DataFrame()
except ConnectionError:
    st.error("Sem ligação à base de dados. Verifique a sua internet e tente novamente.")
    dados      = []
    df_recados = pd.DataFrame()
except Exception as e:
    st.error(f"Erro inesperado ao carregar os dados: {e}")
    dados      = []
    df_recados = pd.DataFrame()

# Paleta de cores para os post-its
POSTIT_COLORS = [
    {"bg": "#fef08a", "text": "#3f6212"},
    {"bg": "#bbf7d0", "text": "#14532d"},
    {"bg": "#fed7aa", "text": "#7c2d12"},
    {"bg": "#fecdd3", "text": "#881337"},
    {"bg": "#bfdbfe", "text": "#1e3a5f"},
    {"bg": "#e9d5ff", "text": "#4c1d95"},
]

# --- 6. MURAL ---
if dados:
    df = pd.DataFrame(dados)
    df['data_nascimento'] = pd.to_datetime(df['data_nascimento'], errors='coerce')
    df_mes = df[df['data_nascimento'].dt.month == mes_atual].copy()

    if not df_mes.empty:
        df_mes = df_mes.sort_values(by='data_nascimento')

        st.markdown(f"""
        <style>
            .block-container {{
                padding-left: 1rem !important;
                padding-right: 1rem !important;
                padding-top: 1rem !important;
                max-width: 100% !important;
            }}
            iframe[title="streamlit_components_v1.html"] {{
                width: 100% !important;
                border: none !important;
            }}
        </style>
        """, unsafe_allow_html=True)

        html_base = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta http-equiv="refresh" content="300">
            <link rel="preconnect" href="https://fonts.googleapis.com">
            <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,700;0,900;1,700&family=Inter:wght@300;400;500;600;700&family=Caveat:wght@500;700&display=swap" rel="stylesheet">
            <style>
                *, *::before, *::after {{
                    margin: 0; padding: 0; box-sizing: border-box;
                }}
                html {{
                    {estilo_fundo}
                    background-attachment: scroll !important;
                    background-repeat: no-repeat !important;
                    background-size: cover !important;
                    background-position: center top !important;
                    min-height: 100%;
                }}
                body {{
                    background: transparent;
                    font-family: 'Inter', sans-serif;
                    color: #f8fafc;
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    padding: 36px 24px 72px;
                    min-height: 100vh;
                    width: 100%;
                }}

                /* ══ HEADER ══════════════════════════════════════════════ */
                .mural-header {{
                    text-align: center;
                    margin-bottom: 52px;
                    position: relative;
                    width: 100%;
                    max-width: min(1400px, 96vw);
                    animation: fadeInDown 0.9s ease both;
                }}
                .mural-header-inner {{
                    background: rgba(255,255,255,0.18);
                    backdrop-filter: blur(22px);
                    -webkit-backdrop-filter: blur(22px);
                    border: 1px solid rgba(255,255,255,0.35);
                    border-radius: 20px;
                    padding: 32px 70px 28px;
                    box-shadow: 0 16px 48px rgba(0,0,0,0.25), inset 0 1px 0 rgba(255,255,255,0.4);
                    display: inline-block;
                    min-width: min(600px, 90vw);
                    position: relative;
                    overflow: hidden;
                }}
                .mural-header-inner::before {{
                    content: ''; position: absolute; top: 0; left: 0; right: 0; height: 4px;
                    background: linear-gradient(90deg, #38bdf8, #818cf8, #f472b6);
                    border-radius: 20px 20px 0 0;
                }}
                .mural-header .subtitulo {{
                    font-family: 'Inter', sans-serif; font-weight: 600; font-size: 0.78rem;
                    letter-spacing: 8px; text-transform: uppercase; color: #ffffff;
                    text-shadow: 0 1px 6px rgba(0,0,0,0.5); margin-bottom: 8px;
                }}
                .mural-header h1 {{
                    font-family: 'Playfair Display', serif; font-size: clamp(2.4rem, 4vw, 3.8rem);
                    font-weight: 900; color: #ffffff; text-shadow: 0 4px 20px rgba(0,0,0,0.6);
                    line-height: 1.15; letter-spacing: -0.5px;
                }}
                .mural-header .mes-destaque {{
                    background: linear-gradient(100deg, #38bdf8 0%, #818cf8 50%, #f472b6 100%);
                    -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
                }}
                .header-deco {{
                    display: flex; justify-content: center; gap: 10px; margin-top: 14px;
                    opacity: 0.6; font-size: 1.2rem; letter-spacing: 4px;
                }}

                @keyframes fadeInDown {{ from {{ opacity: 0; transform: translateY(-20px); }} to {{ opacity: 1; transform: translateY(0); }} }}
                @keyframes fadeInUp {{ from {{ opacity: 0; transform: translateY(40px); }} to {{ opacity: 1; transform: translateY(0); }} }}

                /* ══ GRID ════════════════════════════════════════════════ */
                .mural-grid {{
                    display: flex; flex-direction: column; gap: 28px;
                    max-width: min(1400px, 96vw); width: 100%;
                }}

                /* ══ CARD PRINCIPAL (Fundo Claro Mais Transparente) ══════════════ */
                .aniversariante-row {{
                    display: grid;
                    grid-template-columns: minmax(320px, 1.2fr) 2fr; 
                    gap: clamp(28px, 4vw, 56px);
                    background: rgba(255, 255, 255, 0.65); /* Opacidade reduzida para ficar mais transparente */
                    backdrop-filter: blur(18px);
                    -webkit-backdrop-filter: blur(18px);
                    border: 1px solid rgba(255,255,255,0.6);
                    border-radius: 22px;
                    padding: clamp(30px, 3.5vw, 52px) clamp(28px, 3.5vw, 50px);
                    box-shadow: 0 12px 40px rgba(0,0,0,0.15);
                    animation: fadeInUp 0.7s ease both;
                    align-items: center;
                    min-height: 320px;
                    position: relative;
                    overflow: hidden;
                    transition: transform 0.3s ease, box-shadow 0.3s ease;
                }}
                .aniversariante-row::before {{
                    content: ''; position: absolute; top: 0; left: 0; right: 0; height: 4px;
                    background: linear-gradient(90deg, #38bdf8, #818cf8, #f472b6);
                    border-radius: 20px 20px 0 0;
                }}
                .aniversariante-row:hover {{
                    transform: translateY(-3px); box-shadow: 0 20px 50px rgba(0,0,0,0.25);
                }}
                @media (max-width: 850px) {{
                    .aniversariante-row {{ grid-template-columns: 1fr; padding: 24px; }}
                }}

                /* ══ POLAROID ═══════════════ */
                .polaroid-container {{
                    width: 100%;
                    display: flex;
                    align-items: center;
                    justify-content: center; 
                    padding: 10px;
                }}
                .polaroid-wrapper {{
                    position: relative;
                    width: 100%;
                    max-width: 320px; 
                    display: flex;
                    justify-content: center;
                }}
                .polaroid-wrapper::before {{
                    content: ''; position: absolute; inset: 0; background: rgba(0,0,0,0.08);
                    border-radius: 4px; transform: rotate(4deg) translateY(6px); z-index: 0;
                }}
                .polaroid {{
                    background: #ffffff;
                    padding: 16px 16px 58px;
                    border-radius: 4px;
                    box-shadow: 0 16px 40px rgba(0,0,0,0.15), 0 3px 10px rgba(0,0,0,0.1);
                    width: 100%; 
                    color: #1e293b;
                    text-align: center;
                    position: relative;
                    z-index: 1;
                    transition: transform 0.45s ease;
                }}
                .polaroid::after {{
                    content: ''; position: absolute; top: -14px; left: 50%;
                    transform: translateX(-50%) rotate(-2deg); width: 90px; height: 28px;
                    background: linear-gradient(135deg, rgba(255,255,255,0.9), rgba(255,255,255,0.5));
                    backdrop-filter: blur(4px); box-shadow: 0 2px 6px rgba(0,0,0,0.1);
                    border-radius: 3px; z-index: 5; border: 1px solid rgba(0,0,0,0.05);
                }}
                .polaroid:hover {{ transform: scale(1.04) rotate(1deg); }}
                .foto {{
                    width: 100%; aspect-ratio: 1 / 1; background-size: cover;
                    background-position: center 15%; border-radius: 2px;
                    border: 1px solid #e2e8f0; filter: contrast(1.02) brightness(1.02);
                }}
                .foto-placeholder {{
                    width: 100%; aspect-ratio: 1 / 1; background: linear-gradient(135deg, #f1f5f9, #cbd5e1);
                    display: flex; align-items: center; justify-content: center; font-size: 4.5rem; border-radius: 2px;
                }}
                .nome {{
                    font-family: 'Playfair Display', serif; font-size: clamp(1.2rem, 1.8vw, 1.6rem);
                    font-weight: 900; margin-top: 16px; color: #0f172a; line-height: 1.2;
                }}
                .data-badge {{
                    display: inline-flex; align-items: center; gap: 4px;
                    background: #f1f5f9; color: #0284c7; font-family: 'Inter', sans-serif;
                    font-size: 0.75rem; font-weight: 700; letter-spacing: 1.2px;
                    text-transform: uppercase; padding: 5px 14px; border-radius: 20px;
                    margin-top: 10px; border: 1px solid #e2e8f0;
                }}
                .curiosidade-txt {{
                    font-size: 0.8rem; color: #64748b; margin-top: 12px; font-style: italic;
                    line-height: 1.4; border-top: 1px dashed #cbd5e1; padding-top: 10px;
                }}

                /* ══ RECADOS ═════════════════ */
                .recados-section {{
                    display: flex; flex-direction: column; justify-content: flex-start; min-width: 0;
                }}
                .recados-titulo {{
                    font-family: 'Playfair Display', serif; font-size: clamp(1.3rem, 2vw, 1.9rem);
                    font-weight: 700; font-style: italic;
                    color: #1e293b; 
                    text-shadow: none;
                    margin-bottom: 18px; padding-bottom: 12px;
                    border-bottom: 1px solid rgba(0,0,0,0.1);
                    display: flex; justify-content: space-between; align-items: center; gap: 12px;
                }}
                .recados-titulo-nome {{ color: #0284c7; text-shadow: none; }}
                .area-post-it {{ display: flex; flex-wrap: wrap; gap: 18px; align-content: flex-start; }}
                .post-it {{
                    padding: 18px 15px 14px; width: clamp(140px, 18vw, 175px); min-height: 130px;
                    box-shadow: 4px 6px 15px rgba(0,0,0,0.12), 0 1px 3px rgba(0,0,0,0.05);
                    font-family: 'Caveat', cursive; font-size: 1.05rem; border-radius: 3px 16px 3px 3px;
                    display: flex; flex-direction: column; justify-content: space-between; position: relative;
                    transition: transform 0.28s ease, box-shadow 0.28s ease;
                }}
                .post-it::before {{
                    content: '📌'; position: absolute; top: -12px; left: 50%;
                    transform: translateX(-50%); font-size: 1.2rem; filter: drop-shadow(0 2px 3px rgba(0,0,0,0.2));
                }}
                .post-it:hover {{
                    transform: scale(1.08) translateY(-4px) rotate(1deg) !important; z-index: 10;
                    box-shadow: 6px 15px 25px rgba(0,0,0,0.15);
                }}
                .post-it-msg {{ line-height: 1.35; font-weight: 700; color: rgba(0,0,0,0.85); padding-top: 4px; }}
                .post-it-autor {{
                    font-size: 0.88rem; font-weight: 700; color: rgba(0,0,0,0.6);
                    text-align: right; margin-top: 12px; border-top: 1px dashed rgba(0,0,0,0.15); padding-top: 8px;
                }}
                .sem-recados {{
                    color: #475569; 
                    font-size: 1.05rem; font-style: italic; padding: 28px 0; text-shadow: none;
                    display: flex; align-items: center; gap: 8px;
                }}

                /* ══ BOTÕES DE IMPRESSÃO ═════════════════════════════════ */
                .print-toolbar {{
                    position: fixed; bottom: 30px; right: 30px; display: flex; flex-direction: column; gap: 10px; z-index: 1000;
                }}
                .btn-imprimir {{
                    background: linear-gradient(135deg, #0ea5e9, #38bdf8); color: #0f172a; border: none;
                    padding: 13px 22px; border-radius: 50px; font-family: 'Inter', sans-serif; font-size: 0.9rem;
                    font-weight: 700; box-shadow: 0 8px 20px rgba(14,165,233,0.4), 0 2px 6px rgba(0,0,0,0.3);
                    cursor: pointer; transition: all 0.28s ease; display: flex; align-items: center; gap: 8px;
                }}
                .btn-imprimir:hover {{ transform: translateY(-3px) scale(1.03); box-shadow: 0 14px 28px rgba(14,165,233,0.5); }}
                .btn-paisagem {{ background: linear-gradient(135deg, #6366f1, #818cf8); }}

                /* ══ POSTER A3 PARA IMPRESSÃO (COM FUNDO RESTAURADO) ════ */
                @media print {{
                    * {{ -webkit-print-color-adjust: exact !important; print-color-adjust: exact !important; }}
                    @page {{ size: A3 portrait; margin: 0; }}

                    .btn-imprimir, .print-toolbar, .orientacao-badge {{ display: none !important; }}

                    html, body {{
                        {estilo_fundo} /* <--- DEVOLVE A IMAGEM DE FUNDO/COR AQUI */
                        background-size: cover !important;
                        background-position: center top !important;
                        background-repeat: no-repeat !important;
                        background-attachment: scroll !important;
                        margin: 0 !important; padding: 0 !important;
                        width: 100vw !important; min-height: 100vh !important;
                        font-family: 'Inter', sans-serif !important;
                    }}

                    .mural-header {{ margin-bottom: 0 !important; width: 100% !important; }}
                    
                    /* Cabeçalho agora fica levemente translúcido (quase branco) para se destacar do fundo da imagem */
                    .mural-header-inner {{
                        background: rgba(255,255,255,0.92) !important; color: #0f172a !important; box-shadow: 0 4px 10px rgba(0,0,0,0.1) !important;
                        border: 1px solid rgba(255,255,255,0.8) !important; border-bottom: 4px solid #38bdf8 !important; border-radius: 20px !important;
                        padding: 20px 40px !important; text-align: center !important; width: 100% !important;
                        display: block !important;
                    }}
                    .mural-header-inner::before {{ display: none !important; }}
                    .mural-header .subtitulo {{ color: #64748b !important; font-size: 0.7rem !important; letter-spacing: 6px !important; text-shadow: none !important; }}
                    .mural-header h1 {{ color: #0f172a !important; font-size: 2.2rem !important; text-shadow: none !important; margin: 0 !important; }}
                    .mural-header .mes-destaque {{ -webkit-text-fill-color: #0284c7 !important; background: none !important; }}
                    .header-deco {{ display: none !important; }}

                    .mural-grid {{
                        display: grid !important; grid-template-columns: repeat(var(--cols, 2), 1fr) !important;
                        grid-template-rows: repeat(var(--rows, 3), 1fr) !important; gap: 20px !important;
                        padding: 20px !important; width: 100% !important; 
                        background: transparent !important; /* <--- PERMITE VER A IMAGEM DE FUNDO NA GRELHA */
                    }}

                    /* O cartão individual fica quase branco sólido para garantir total legibilidade do texto por cima da imagem */
                    .aniversariante-row {{
                        display: flex !important; flex-direction: column !important; align-items: center !important;
                        background: rgba(255,255,255,0.92) !important; border: 1px solid rgba(255,255,255,0.9) !important;
                        border-top: 5px solid #38bdf8 !important; border-radius: 16px !important;
                        padding: 0 !important; box-shadow: 0 4px 15px rgba(0,0,0,0.1) !important; break-inside: avoid !important;
                        page-break-inside: avoid !important; overflow: hidden !important; height: 100% !important;
                    }}
                    .aniversariante-row::before {{ display: none !important; }}

                    .polaroid-container {{
                        width: 100% !important; display: flex !important; flex-direction: column !important;
                        align-items: center !important; padding: 25px 20px 10px !important;
                    }}
                    .polaroid-wrapper {{ width: 100% !important; display: flex !important; justify-content: center !important; }}
                    .polaroid-wrapper::before {{ display: none !important; }}
                    .polaroid {{
                        width: 100% !important; max-width: 240px !important; 
                        padding: 12px 12px 40px !important; box-shadow: 0 4px 15px rgba(0,0,0,0.1) !important;
                        background: white !important; border: 1px solid #cbd5e1 !important; border-radius: 4px !important;
                    }}
                    .polaroid::after {{ display: none !important; }}

                    .foto {{ aspect-ratio: 3 / 4 !important; width: 100% !important; }}
                    .nome {{ font-size: 1.2rem !important; font-weight: 900 !important; color: #0f172a !important; margin-top: 12px !important; text-shadow: none !important; }}
                    .data-badge {{ font-size: 0.75rem !important; background: transparent !important; color: #0284c7 !important; border: 1px solid #0284c7 !important; font-weight: 800 !important; padding: 4px 12px !important; }}
                    .curiosidade-txt {{ font-size: 0.7rem !important; color: #475569 !important; }}

                    .recados-section {{
                        width: 100% !important; display: flex !important; flex-direction: column !important;
                        padding: 15px !important; background: transparent !important; border-top: 1px solid #e2e8f0 !important;
                    }}
                    .recados-titulo {{
                        color: #0f172a !important; text-shadow: none !important; font-size: 0.95rem !important;
                        border-bottom: 1px solid #cbd5e1 !important; margin-bottom: 12px !important;
                    }}
                    .recados-titulo-nome {{ color: #0284c7 !important; -webkit-text-fill-color: #0284c7 !important; }}
                    .area-post-it {{ display: flex !important; flex-wrap: wrap !important; justify-content: center !important; gap: 8px !important; }}
                    .post-it {{ width: clamp(80px, 30%, 120px) !important; min-height: 85px !important; padding: 12px 8px 8px !important; box-shadow: 2px 3px 6px rgba(0,0,0,0.1) !important; border: 1px solid rgba(0,0,0,0.05) !important; }}
                    .post-it::before, .post-it::after {{ display: none !important; }}
                    .post-it-msg {{ font-size: 0.75rem !important; color: rgba(0,0,0,0.9) !important; }}
                    .post-it-autor {{ font-size: 0.7rem !important; color: rgba(0,0,0,0.7) !important; }}
                    .sem-recados {{ color: #64748b !important; text-shadow: none !important; font-size: 0.85rem !important; }}
                }}
        </style>
        <style id="orientacao-style">
            @media print {{ @page {{ size: A3 portrait; margin: 0; }} }}
        </style>
        </head>
        <body>
            <script>
                var IS_TV = {'true' if is_tv else 'false'};
                var orientacao = 'portrait';

                function calcGridVars(isLandscape) {{
                    var cards = document.querySelectorAll('.aniversariante-row').length;
                    var cols, rows;
                    if (isLandscape) {{
                        if      (cards <= 1) {{ cols = 1; rows = 1; }}
                        else if (cards == 2) {{ cols = 2; rows = 1; }}
                        else if (cards == 3) {{ cols = 3; rows = 1; }}
                        else if (cards == 4) {{ cols = 4; rows = 1; }}
                        else if (cards == 5) {{ cols = 3; rows = 2; }}
                        else                {{ cols = 3; rows = 2; }}
                    }} else {{
                        if      (cards <= 1) {{ cols = 1; rows = 1; }}
                        else if (cards == 2) {{ cols = 2; rows = 1; }}
                        else if (cards == 3) {{ cols = 3; rows = 1; }}
                        else if (cards == 4) {{ cols = 2; rows = 2; }}
                        else if (cards == 5) {{ cols = 3; rows = 2; }}
                        else                {{ cols = 2; rows = 3; }}
                    }}
                    return {{ cols: cols, rows: rows }};
                }}

                function applyOrientation(ori) {{
                    orientacao = ori;
                    var isLandscape = (ori === 'landscape');
                    var styleEl = document.getElementById('orientacao-style');
                    styleEl.textContent = '@media print {{ @page {{ size: A3 ' + ori + '; margin: 0; }} }}';

                    var v = calcGridVars(isLandscape);
                    var grid = document.querySelector('.mural-grid');
                    if (grid) {{
                        grid.style.setProperty('--cols', v.cols);
                        grid.style.setProperty('--rows', v.rows);
                    }}

                    var badge = document.getElementById('badge-orientacao');
                    badge.textContent = isLandscape ? '↔ PAISAGEM A3' : '↕ RETRATO A3';
                    badge.style.display = 'block';
                }}

                function imprimirCom(ori) {{
                    applyOrientation(ori);
                    setTimeout(function() {{ window.print(); }}, 80);
                }}

                document.addEventListener('DOMContentLoaded', function() {{
                    applyOrientation('portrait');
                    if (IS_TV) {{
                        var toolbar = document.querySelector('.print-toolbar');
                        var badge   = document.getElementById('badge-orientacao');
                        if (toolbar) toolbar.style.display = 'none';
                        if (badge)   badge.style.display   = 'none';
                    }}
                }});
            </script>

            <div id="badge-orientacao" class="orientacao-badge"></div>
            <div class="print-toolbar">
                <button class="btn-imprimir" onclick="imprimirCom('portrait')">🖨️ Imprimir A3 — Retrato</button>
                <button class="btn-imprimir btn-paisagem" onclick="imprimirCom('landscape')">🖨️ Imprimir A3 — Paisagem</button>
            </div>

            <div class="mural-header">
                <div class="mural-header-inner">
                    <p class="subtitulo">✦ Celebrações GAFI ✦</p>
                    <h1>Aniversariantes de <span class="mes-destaque">{nome_mes_atual}</span></h1>
                    <div class="header-deco">🎉 🎂 🎈 🎊 🎁</div>
                </div>
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
                curiosidade_html = f'<div class="curiosidade-txt">"{texto_curiosidade}"</div>'

            post_its_html = ""
            if not df_recados.empty and 'para_quem' in df_recados.columns:
                recados_pessoa = df_recados[df_recados['para_quem'] == nome]
                if recados_pessoa.empty:
                    post_its_html = '<p class="sem-recados">📌 Seja o primeiro a deixar um recado!</p>'
                else:
                    for i, (_, recado) in enumerate(recados_pessoa.iterrows()):
                        mensagem = str(recado.get("mensagem", "")).strip()
                        autor    = str(recado.get("de_quem", "Anônimo")).strip()
                        rotacao  = random.randint(-4, 4)
                        cor      = POSTIT_COLORS[i % len(POSTIT_COLORS)]
                        post_its_html += f"""
                        <div class="post-it"
                             style="background-color:{cor['bg']}; transform: rotate({rotacao}deg);">
                            <div class="post-it-msg">{mensagem}</div>
                            <div class="post-it-autor">~ {autor}</div>
                        </div>
                        """
            else:
                post_its_html = '<p class="sem-recados">📌 Seja o primeiro a deixar um recado!</p>'

            delay = idx * 0.2

            cartoes_html += f"""
            <div class="aniversariante-row" style="animation-delay: {delay}s;">
                <div class="polaroid-container">
                    <div class="polaroid-wrapper">
                        <div class="polaroid">
                            {foto_html}
                            <div class="nome">{nome}</div>
                            <div class="data-badge">🎉 {dia} de {nome_mes_atual}</div>
                            {curiosidade_html}
                        </div>
                    </div>
                </div>
                
                <div class="recados-section">
                    <div class="recados-titulo">
                        <span>Mensagens para <span class="recados-titulo-nome">{nome.split()[0]}</span></span>
                        <span style="font-size: 1.7rem; opacity:0.9; flex-shrink:0; font-style: normal;">🎂</span>
                    </div>
                    <div class="area-post-it">
                        {post_its_html}
                    </div>
                </div>
            </div>
            """

        full_html = html_base + cartoes_html + "</div></body></html>"
        altura_iframe = max(1200, len(df_mes) * 550 + 300)
        components.html(full_html, height=altura_iframe, scrolling=True)

    else:
        st.info(f"🗓️ Nenhum aniversariante cadastrado para {nome_mes_atual}.")
else:
    st.warning("⚠️ Nenhum dado encontrado no banco de dados.")
