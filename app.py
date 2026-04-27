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
            # Garante que o valor vai como texto para o banco
            valor_str = str(valor)
            
            # 1. Verifica se a chave já existe na tabela
            busca = supabase.table("configuracoes_mural").select("id").eq("chave", chave).execute()
            
            if busca.data and len(busca.data) > 0:
                # 2. Se a chave existir, atualiza o valor
                supabase.table("configuracoes_mural").update({"valor": valor_str}).eq("chave", chave).execute()
            else:
                # 3. Se a chave não existir, insere um novo registro
                supabase.table("configuracoes_mural").insert({"chave": chave, "valor": valor_str}).execute()
                    
        except Exception as e:
            st.error(f"Erro ao salvar configuração: {e}")
            raise e

    # Recarrega sempre do banco antes de renderizar os inputs do admin
    config = carregar_config()
    exibir_mural = to_bool(config.get("exibir_mural", False))
    liberar_recados = to_bool(config.get("liberar_recados", False))
    liberar_cadastro = to_bool(config.get("liberar_cadastro", True))

    st.sidebar.divider()
    
    # Agrupando os controles de acesso
    with st.sidebar.expander("🔐 Controles de Acesso", expanded=True):
        novo_cadastro = st.checkbox("Liberar Aba de Cadastro", value=liberar_cadastro)
        novo_recados = st.checkbox("Liberar Aba de Recados", value=liberar_recados)
        novo_exibir = st.checkbox("🎉 REVELAR MURAL FINAL", value=exibir_mural)

    # Agrupando a personalização de cores e imagens
    with st.sidebar.expander("🎨 Personalização Visual", expanded=False):
        cor_fundo_banco = config.get("cor_fundo")
        if cor_hex_valida(cor_fundo_banco):
            cor_fundo = st.color_picker("Cor base do Mural", value=cor_fundo_banco)
        else:
            cor_fundo = st.color_picker("Cor base do Mural")
            
        imagem_fundo  = st.file_uploader("Imagem de Fundo", type=["jpg", "png", "jpeg"])

    # Lê o arquivo UMA ÚNICA VEZ e reutiliza
    img_bytes_admin  = None
    img_b64_admin    = None
    img_tipo_admin   = None
    if imagem_fundo is not None:
        img_bytes_admin = imagem_fundo.read()
        img_b64_admin   = base64.b64encode(img_bytes_admin).decode()
        img_tipo_admin  = imagem_fundo.type

    st.sidebar.write("") # Espaçamento
    # Botão de salvar mais destacado ocupando toda a largura
    if st.sidebar.button("💾 Salvar alterações", type="primary", use_container_width=True):
        atualizar_config("liberar_cadastro", novo_cadastro)
        atualizar_config("liberar_recados",  novo_recados)
        atualizar_config("exibir_mural",     novo_exibir)
        atualizar_config("cor_fundo",        cor_fundo)
        if img_b64_admin is not None:
            fundo_data_url = f"data:{img_tipo_admin};base64,{img_b64_admin}"
            atualizar_config("imagem_fundo", fundo_data_url)
        # Depois de salvar, buscar novamente do banco para evitar dependência de sessão
        config = carregar_config()
        st.sidebar.success("Atualizado!")
        st.rerun()

    # Preview do fundo para o admin
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
        /* Aplica o fundo escolhido no admin também na tela de espera */
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
        .emoji-animado {{
            font-size: 5rem;
            display: inline-block;
            animation: pulse 2s infinite;
            margin-bottom: 10px;
            filter: drop-shadow(0 4px 6px rgba(0,0,0,0.3));
        }}
        .porteiro-titulo {{
            font-family: 'Playfair Display', serif;
            font-size: 2.5rem;
            font-weight: 700;
            margin-bottom: 15px;
            text-shadow: 0 2px 8px rgba(0,0,0,0.7);
        }}
        .porteiro-texto {{
            font-family: 'Lato', sans-serif;
            font-size: 1.1rem;
            line-height: 1.6;
            color: #e2e8f0;
            text-shadow: 0 1px 4px rgba(0,0,0,0.7);
        }}
        @keyframes pulse {{
            0% {{ transform: scale(1); }}
            50% {{ transform: scale(1.15) rotate(-5deg); }}
            100% {{ transform: scale(1); }}
        }}
        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(20px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
    </style>

    <div class="porteiro-card">
        <div class="emoji-animado">🤫</div>
        <div class="porteiro-titulo">Mural em Preparação</div>
        <div class="porteiro-texto">
            A equipe está cuidando de cada detalhe com muito carinho!<br><br>
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
    with st.spinner("Carregando mural..."):
        response     = supabase.table("aniversariantes").select("*").execute()
        dados        = response.data or []
        resp_recados = supabase.table("recados").select("*").execute()
        df_recados   = pd.DataFrame(resp_recados.data) if resp_recados.data else pd.DataFrame()
except ConnectionError:
    st.error("Sem conexão com o banco de dados. Verifique sua internet e tente novamente.")
    dados      = []
    df_recados = pd.DataFrame()
except Exception as e:
    st.error(f"Erro inesperado ao carregar os dados: {e}")
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

        # ── FUNDO aplicado no .stApp (tela de porteiro e fundo geral) ───────────
        # Para o mural, o fundo vai DENTRO do iframe com background-size: cover
        # e background-attachment: scroll (fixed causa cortes no iframe).
        # Também remove o padding do Streamlit para o iframe ocupar mais tela.
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

        # Prepara a variável de fundo EXCLUSIVA para os cartões na hora da impressão
        img_print = config.get("imagem_fundo", "")
        cor_print = config.get("cor_fundo", "")
        if img_print:
            estilo_fundo_print = f"background-image: url('{img_print}') !important; background-size: cover !important; background-position: center !important;"
        elif cor_hex_valida(cor_print):
            estilo_fundo_print = f"background-color: {cor_print} !important;"
        else:
            estilo_fundo_print = "background-color: #334155 !important;"

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
                    background: linear-gradient(135deg,
                        rgba(15,23,42,0.72) 0%,
                        rgba(30,41,59,0.60) 50%,
                        rgba(15,23,42,0.72) 100%);
                    backdrop-filter: blur(20px);
                    -webkit-backdrop-filter: blur(20px);
                    border: 1px solid rgba(255,255,255,0.12);
                    border-top: 3px solid;
                    border-image: linear-gradient(90deg, #38bdf8, #818cf8, #f472b6) 1;
                    border-radius: 0 0 24px 24px;
                    padding: 32px 70px 28px;
                    box-shadow:
                        0 20px 50px rgba(0,0,0,0.4),
                        inset 0 1px 0 rgba(255,255,255,0.08);
                    display: inline-block;
                    min-width: min(600px, 90vw);
                }}
                .mural-header .subtitulo {{
                    font-family: 'Inter', sans-serif;
                    font-weight: 500;
                    font-size: 0.78rem;
                    letter-spacing: 8px;
                    text-transform: uppercase;
                    color: #94a3b8;
                    margin-bottom: 8px;
                }}
                .mural-header h1 {{
                    font-family: 'Playfair Display', serif;
                    font-size: clamp(2.4rem, 4vw, 3.8rem);
                    font-weight: 900;
                    color: #ffffff;
                    text-shadow: 0 4px 20px rgba(0,0,0,0.6);
                    line-height: 1.15;
                    letter-spacing: -0.5px;
                }}
                .mural-header .mes-destaque {{
                    background: linear-gradient(100deg, #38bdf8 0%, #818cf8 50%, #f472b6 100%);
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                    background-clip: text;
                }}
                .header-deco {{
                    display: flex;
                    justify-content: center;
                    gap: 10px;
                    margin-top: 14px;
                    opacity: 0.6;
                    font-size: 1.2rem;
                    letter-spacing: 4px;
                }}

                @keyframes fadeInDown {{
                    from {{ opacity: 0; transform: translateY(-20px); }}
                    to   {{ opacity: 1; transform: translateY(0); }}
                }}
                @keyframes fadeInUp {{
                    from {{ opacity: 0; transform: translateY(40px); }}
                    to   {{ opacity: 1; transform: translateY(0); }}
                }}
                @keyframes shimmer {{
                    0%   {{ background-position: -200% center; }}
                    100% {{ background-position: 200% center; }}
                }}

                /* ══ GRID ════════════════════════════════════════════════ */
                .mural-grid {{
                    display: flex;
                    flex-direction: column;
                    gap: 28px;
                    max-width: min(1400px, 96vw);
                    width: 100%;
                }}

                /* ══ CARD PRINCIPAL ══════════════════════════════════════ */
                .aniversariante-row {{
                    display: grid;
                    grid-template-columns: auto 1fr;
                    gap: clamp(24px, 3.5vw, 48px);
                    background: rgba(255,255,255,0.13);
                    backdrop-filter: blur(16px);
                    -webkit-backdrop-filter: blur(16px);
                    border: 1px solid rgba(255,255,255,0.28);
                    border-radius: 20px;
                    padding: clamp(28px, 3.5vw, 50px);
                    box-shadow:
                        0 12px 36px rgba(0,0,0,0.22),
                        0 1px 0 rgba(255,255,255,0.18) inset;
                    animation: fadeInUp 0.7s ease both;
                    align-items: center;
                    position: relative;
                    overflow: hidden;
                    transition: transform 0.3s ease, box-shadow 0.3s ease;
                }}
                .aniversariante-row::before {{
                    content: '';
                    position: absolute;
                    top: 0; left: 0; right: 0;
                    height: 3px;
                    background: linear-gradient(90deg, #38bdf8, #818cf8, #f472b6);
                    border-radius: 20px 20px 0 0;
                }}
                .aniversariante-row:hover {{
                    transform: translateY(-3px);
                    box-shadow: 0 28px 60px rgba(0,0,0,0.50);
                }}
                @media (max-width: 760px) {{
                    .aniversariante-row {{
                        grid-template-columns: 1fr;
                        padding: 24px;
                    }}
                }}

                /* ══ POLAROID ════════════════════════════════════════════ */
                .polaroid-container {{
                    flex-shrink: 0;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    align-self: center;
                }}
                .polaroid-wrapper {{
                    position: relative;
                }}
                /* Sombra decorativa atrás */
                .polaroid-wrapper::before {{
                    content: '';
                    position: absolute;
                    inset: 0;
                    background: white;
                    border-radius: 4px;
                    transform: rotate(4deg) translateY(4px);
                    opacity: 0.18;
                    z-index: 0;
                }}
                .polaroid {{
                    background: #ffffff;
                    padding: 14px 14px 56px;
                    border-radius: 4px;
                    box-shadow:
                        0 14px 36px rgba(0,0,0,0.40),
                        0 2px 8px rgba(0,0,0,0.18),
                        inset 0 1px 0 rgba(255,255,255,1);
                    width: clamp(200px, 24vw, 310px);
                    color: #1e293b;
                    text-align: center;
                    position: relative;
                    z-index: 1;
                    transition: transform 0.45s cubic-bezier(0.175, 0.885, 0.32, 1.275);
                }}
                /* Fita adesiva */
                .polaroid::after {{
                    content: '';
                    position: absolute;
                    top: -14px;
                    left: 50%;
                    transform: translateX(-50%) rotate(-2deg);
                    width: 90px;
                    height: 28px;
                    background: linear-gradient(135deg,
                        rgba(255,255,255,0.55),
                        rgba(255,255,255,0.30));
                    backdrop-filter: blur(4px);
                    box-shadow: 0 2px 6px rgba(0,0,0,0.15);
                    border-radius: 3px;
                    z-index: 5;
                    border: 1px solid rgba(255,255,255,0.6);
                }}
                .polaroid:hover {{
                    transform: scale(1.06) rotate(2deg);
                }}
                .foto {{
                    width: 100%;
                    aspect-ratio: 1 / 1;
                    background-size: cover;
                    background-position: center 15%;
                    border-radius: 2px;
                    border: 1px solid #e2e8f0;
                    filter: contrast(1.06) brightness(1.02) saturate(1.05);
                }}
                .foto-placeholder {{
                    width: 100%;
                    aspect-ratio: 1 / 1;
                    background: linear-gradient(135deg, #f1f5f9, #cbd5e1);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-size: 4.5rem;
                    border-radius: 2px;
                }}
                .nome {{
                    font-family: 'Playfair Display', serif;
                    font-size: clamp(1.15rem, 1.7vw, 1.55rem);
                    font-weight: 900;
                    margin-top: 14px;
                    color: #0f172a;
                    line-height: 1.2;
                }}
                .data-badge {{
                    display: inline-flex;
                    align-items: center;
                    gap: 4px;
                    background: linear-gradient(135deg, #0f172a, #1e293b);
                    color: #38bdf8;
                    font-family: 'Inter', sans-serif;
                    font-size: 0.72rem;
                    font-weight: 700;
                    letter-spacing: 1.5px;
                    text-transform: uppercase;
                    padding: 5px 14px;
                    border-radius: 20px;
                    margin-top: 8px;
                    border: 1px solid rgba(56,189,248,0.3);
                }}
                .curiosidade-txt {{
                    font-size: 0.78rem;
                    color: #64748b;
                    margin-top: 10px;
                    font-style: italic;
                    line-height: 1.4;
                    border-top: 1px dashed #cbd5e1;
                    padding-top: 8px;
                }}

                /* ══ RECADOS ═════════════════════════════════════════════ */
                .recados-section {{
                    display: flex;
                    flex-direction: column;
                    justify-content: flex-start;
                    min-width: 0;
                }}
                .recados-titulo {{
                    font-family: 'Playfair Display', serif;
                    font-size: clamp(1.3rem, 2vw, 1.9rem);
                    font-weight: 700;
                    font-style: italic;
                    color: #f1f5f9;
                    text-shadow: 0 2px 8px rgba(0,0,0,0.6);
                    margin-bottom: 18px;
                    padding-bottom: 12px;
                    border-bottom: 1px solid rgba(255,255,255,0.14);
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    gap: 12px;
                }}
                .recados-titulo-nome {{
                    background: linear-gradient(100deg, #e2e8f0, #bae6fd);
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                    background-clip: text;
                }}
                .area-post-it {{
                    display: flex;
                    flex-wrap: wrap;
                    gap: 18px;
                    align-content: flex-start;
                }}
                .post-it {{
                    padding: 18px 15px 14px;
                    width: clamp(140px, 18vw, 175px);
                    min-height: 130px;
                    box-shadow:
                        4px 6px 18px rgba(0,0,0,0.22),
                        0 1px 3px rgba(0,0,0,0.12);
                    font-family: 'Caveat', cursive;
                    font-size: 1.05rem;
                    border-radius: 3px 16px 3px 3px;
                    display: flex;
                    flex-direction: column;
                    justify-content: space-between;
                    position: relative;
                    transition: transform 0.28s ease, box-shadow 0.28s ease;
                    background-image: linear-gradient(160deg,
                        rgba(255,255,255,0.50) 0%,
                        rgba(255,255,255,0.08) 100%) !important;
                }}
                /* Pino decorativo */
                .post-it::before {{
                    content: '📌';
                    position: absolute;
                    top: -12px;
                    left: 50%;
                    transform: translateX(-50%);
                    font-size: 1rem;
                    filter: drop-shadow(0 2px 3px rgba(0,0,0,0.3));
                }}
                .post-it:hover {{
                    transform: scale(1.12) translateY(-6px) rotate(1deg) !important;
                    z-index: 10;
                    box-shadow: 6px 18px 30px rgba(0,0,0,0.32);
                }}
                .post-it-msg {{
                    line-height: 1.35;
                    font-weight: 700;
                    color: rgba(0,0,0,0.88);
                    padding-top: 4px;
                }}
                .post-it-autor {{
                    font-size: 0.88rem;
                    font-weight: 700;
                    color: rgba(0,0,0,0.55);
                    text-align: right;
                    margin-top: 12px;
                    border-top: 1px dashed rgba(0,0,0,0.15);
                    padding-top: 8px;
                }}
                .sem-recados {{
                    color: rgba(255,255,255,0.65);
                    font-size: 0.95rem;
                    font-style: italic;
                    padding: 22px 0;
                    text-shadow: 0 1px 4px rgba(0,0,0,0.6);
                    display: flex;
                    align-items: center;
                    gap: 8px;
                    opacity: 0.8;
                }}

                /* ══ BOTÕES DE IMPRESSÃO ═════════════════════════════════ */
                .print-toolbar {{
                    position: fixed;
                    bottom: 30px;
                    right: 30px;
                    display: flex;
                    flex-direction: column;
                    gap: 10px;
                    z-index: 1000;
                }}
                .btn-imprimir {{
                    background: linear-gradient(135deg, #0ea5e9, #38bdf8);
                    color: #0f172a;
                    border: none;
                    padding: 13px 22px;
                    border-radius: 50px;
                    font-family: 'Inter', sans-serif;
                    font-size: 0.9rem;
                    font-weight: 700;
                    box-shadow:
                        0 8px 20px rgba(14,165,233,0.4),
                        0 2px 6px rgba(0,0,0,0.3);
                    cursor: pointer;
                    transition: all 0.28s ease;
                    display: flex;
                    align-items: center;
                    gap: 8px;
                    white-space: nowrap;
                    letter-spacing: 0.3px;
                }}
                .btn-imprimir:hover {{
                    transform: translateY(-3px) scale(1.03);
                    box-shadow: 0 14px 28px rgba(14,165,233,0.5);
                }}
                .btn-paisagem {{
                    background: linear-gradient(135deg, #6366f1, #818cf8);
                    box-shadow: 0 8px 20px rgba(99,102,241,0.4), 0 2px 6px rgba(0,0,0,0.3);
                }}
                .btn-paisagem:hover {{
                    box-shadow: 0 14px 28px rgba(99,102,241,0.5);
                }}
                .orientacao-badge {{
                    position: fixed;
                    bottom: 145px;
                    right: 30px;
                    background: rgba(15,23,42,0.85);
                    color: #94a3b8;
                    font-family: 'Inter', sans-serif;
                    font-size: 0.72rem;
                    padding: 4px 14px;
                    border-radius: 20px;
                    z-index: 1001;
                    letter-spacing: 1.5px;
                    display: none;
                    border: 1px solid rgba(255,255,255,0.1);
                }}

                /* ══ POSTER A3 PARA IMPRESSÃO ══════════════════════════ */
                @media print {{
                    * {{
                        -webkit-print-color-adjust: exact !important;
                        print-color-adjust: exact !important;
                    }}
                    @page {{
                        size: A3 portrait;
                        margin: 0;
                    }}

                    .btn-imprimir, .print-toolbar, .orientacao-badge {{ display: none !important; }}

                    html {{
                        {estilo_fundo}
                        background-attachment: scroll !important;
                        background-size: cover !important;
                        background-position: center top !important;
                        background-repeat: no-repeat !important;
                    }}

                    body {{
                        margin: 0 !important;
                        padding: 0 !important;
                        display: flex !important;
                        flex-direction: column !important;
                        width: 100vw !important;
                        min-height: 100vh !important;
                        background: transparent !important;
                        font-family: 'Inter', sans-serif !important;
                    }}

                    .mural-header {{
                        margin-bottom: 0 !important;
                        width: 100% !important;
                        flex-shrink: 0 !important;
                    }}
                    .mural-header-inner {{
                        background: rgba(0,0,0,0.55) !important;
                        backdrop-filter: none !important;
                        color: white !important;
                        box-shadow: none !important;
                        border: none !important;
                        border-bottom: 3px solid #38bdf8 !important;
                        border-radius: 0 !important;
                        padding: 18px 40px 14px !important;
                        text-align: center !important;
                        width: 100% !important;
                        box-sizing: border-box !important;
                        display: block !important;
                    }}
                    .mural-header .subtitulo {{
                        color: #94a3b8 !important;
                        font-size: 0.65rem !important;
                        letter-spacing: 6px !important;
                        margin-bottom: 4px !important;
                    }}
                    .mural-header h1 {{
                        color: white !important;
                        font-size: 2.2rem !important;
                        text-shadow: 0 2px 8px rgba(0,0,0,0.6) !important;
                        margin: 0 !important;
                    }}
                    .mural-header .mes-destaque {{
                        -webkit-text-fill-color: #38bdf8 !important;
                        background: none !important;
                    }}
                    .header-deco {{ display: none !important; }}

                    .mural-grid {{
                        display: grid !important;
                        grid-template-columns: repeat(var(--cols, 2), 1fr) !important;
                        grid-template-rows: repeat(var(--rows, 3), 1fr) !important;
                        gap: 10px !important;
                        padding: 12px !important;
                        width: 100% !important;
                        flex-grow: 1 !important;
                        box-sizing: border-box !important;
                        align-items: stretch !important;
                    }}

                    .aniversariante-row:nth-child(6n) {{
                        page-break-after: always !important;
                        break-after: page !important;
                    }}
                    .aniversariante-row {{
                        display: flex !important;
                        flex-direction: column !important;
                        align-items: center !important;
                        background: rgba(255,255,255,0.18) !important;
                        backdrop-filter: none !important;
                        border: 1.5px solid rgba(255,255,255,0.35) !important;
                        border-top: 4px solid #38bdf8 !important;
                        border-radius: 12px !important;
                        padding: 0 !important;
                        box-shadow: 0 4px 16px rgba(0,0,0,0.35) !important;
                        break-inside: avoid !important;
                        page-break-inside: avoid !important;
                        overflow: hidden !important;
                        height: 100% !important;
                        transition: none !important;
                    }}
                    .aniversariante-row::before {{ display: none !important; }}
                    .aniversariante-row:hover {{ transform: none !important; box-shadow: 0 4px 16px rgba(0,0,0,0.5) !important; }}

                    .polaroid-container {{
                        width: 100% !important;
                        display: flex !important;
                        flex-direction: column !important;
                        align-items: center !important;
                        padding: 16px 16px 10px !important;
                        flex-shrink: 0 !important;
                    }}
                    .polaroid-wrapper::before {{ display: none !important; }}
                    .polaroid {{
                        width: clamp(100px, 42%, 175px) !important;
                        padding: 8px 8px 36px !important;
                        box-shadow: 0 6px 18px rgba(0,0,0,0.45) !important;
                        transform: none !important;
                        transition: none !important;
                        background: white !important;
                        border-radius: 3px !important;
                    }}
                    .polaroid::after {{ display: none !important; }}
                    .polaroid:hover {{ transform: none !important; }}

                    .foto {{
                        aspect-ratio: 3 / 4 !important;
                        width: 100% !important;
                    }}
                    .foto-placeholder {{
                        aspect-ratio: 3 / 4 !important;
                        width: 100% !important;
                        font-size: 2.2rem !important;
                    }}
                    .nome {{
                        font-size: 1rem !important;
                        font-weight: 900 !important;
                        color: #0f172a !important;
                        margin-top: 10px !important;
                        text-align: center !important;
                        text-shadow: none !important;
                    }}
                    .data-badge {{
                        font-size: 0.65rem !important;
                        background: #38bdf8 !important;
                        color: #0f172a !important;
                        font-weight: 800 !important;
                        margin-top: 5px !important;
                        padding: 3px 10px !important;
                        border: none !important;
                    }}
                    .curiosidade-txt {{
                        font-size: 0.62rem !important;
                        color: #94a3b8 !important;
                        margin-top: 7px !important;
                    }}

                    .recados-section {{
                        flex-grow: 1 !important;
                        width: 100% !important;
                        display: flex !important;
                        flex-direction: column !important;
                        justify-content: flex-start !important;
                        padding: 8px 14px 14px !important;
                        box-sizing: border-box !important;
                        background: rgba(0,0,0,0.25) !important;
                    }}
                    .recados-titulo {{
                        color: #ffffff !important;
                        text-shadow: 0 1px 6px rgba(0,0,0,0.9) !important;
                        font-size: 0.82rem !important;
                        font-weight: 700 !important;
                        font-style: normal !important;
                        border-bottom: 1px solid rgba(255,255,255,0.35) !important;
                        margin-bottom: 8px !important;
                        padding-bottom: 5px !important;
                        width: 100% !important;
                        display: flex !important;
                        align-items: center !important;
                        gap: 4px !important;
                        justify-content: center !important;
                    }}
                    .recados-titulo-nome {{
                        -webkit-text-fill-color: #bae6fd !important;
                        background: none !important;
                    }}
                    .area-post-it {{
                        display: flex !important;
                        flex-wrap: wrap !important;
                        justify-content: center !important;
                        gap: 6px !important;
                    }}
                    .post-it {{
                        width: clamp(70px, 26%, 110px) !important;
                        min-height: 72px !important;
                        font-size: 0.72rem !important;
                        padding: 14px 7px 7px !important;
                        box-shadow: 2px 3px 8px rgba(0,0,0,0.25) !important;
                        transform: none !important;
                        border-radius: 2px 8px 2px 2px !important;
                    }}
                    .post-it::before {{ display: none !important; }}
                    .post-it::after {{ display: none !important; }}
                    .post-it:hover {{ transform: none !important; }}
                    .post-it-msg {{
                        font-size: 0.72rem !important;
                        line-height: 1.3 !important;
                        color: rgba(0,0,0,0.85) !important;
                    }}
                    .post-it-autor {{
                        font-size: 0.65rem !important;
                        margin-top: 6px !important;
                        color: rgba(0,0,0,0.60) !important;
                        border-top: 1px dashed rgba(0,0,0,0.15) !important;
                        padding-top: 4px !important;
                    }}
                    .sem-recados {{
                        color: rgba(255,255,255,0.70) !important;
                        text-shadow: 0 1px 3px rgba(0,0,0,0.6) !important;
                        font-size: 0.75rem !important;
                        padding: 6px 0 !important;
                        text-align: center !important;
                        display: block !important;
                    }}
                }}
        </style>
        <style id="orientacao-style">
            /* Estilo de @page dinâmico — sobrescrito via JS */
            @media print {{ @page {{ size: A3 portrait; margin: 0; }} }}
        </style>
        </head>
        <body>
            <script>
                // ── Modo TV: esconde toolbar de impressão ──────────────────────
                var IS_TV = {'true' if is_tv else 'false'};

                // ── Orientação e grade adaptativa ──────────────────────────────
                var orientacao = 'portrait'; // padrão

                function calcGridVars(isLandscape) {{
                    var cards = document.querySelectorAll('.aniversariante-row').length;
                    var cols, rows;
                    if (isLandscape) {{
                        // Paisagem: mais colunas, menos linhas
                        if      (cards <= 1) {{ cols = 1; rows = 1; }}
                        else if (cards == 2) {{ cols = 2; rows = 1; }}
                        else if (cards == 3) {{ cols = 3; rows = 1; }}
                        else if (cards == 4) {{ cols = 4; rows = 1; }}
                        else if (cards == 5) {{ cols = 3; rows = 2; }}
                        else                {{ cols = 3; rows = 2; }}
                    }} else {{
                        // Retrato: layout original
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

                    // Atualiza @page via <style> injetado no <head>
                    var styleEl = document.getElementById('orientacao-style');
                    styleEl.textContent = '@media print {{ @page {{ size: A3 ' + ori + '; margin: 0; }} }}';

                    // Atualiza grid
                    var v = calcGridVars(isLandscape);
                    var grid = document.querySelector('.mural-grid');
                    if (grid) {{
                        grid.style.setProperty('--cols', v.cols);
                        grid.style.setProperty('--rows', v.rows);
                    }}

                    // Atualiza badge
                    var badge = document.getElementById('badge-orientacao');
                    badge.textContent = isLandscape ? '↔ PAISAGEM A3' : '↕ RETRATO A3';
                    badge.style.display = 'block';
                }}

                function imprimirCom(ori) {{
                    applyOrientation(ori);
                    setTimeout(function() {{ window.print(); }}, 80);
                }}

                // Inicializa com retrato ao carregar
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

            # ── Post-its ──
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

            delay = idx * 0.2 # Atraso na animação para entrada em cascata

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
                        <span style="font-size: 1.7rem; opacity:0.9; flex-shrink:0;">🎂</span>
                    </div>
                    <div class="area-post-it">
                        {post_its_html}
                    </div>
                </div>
            </div>
            """

        full_html = html_base + cartoes_html + "</div></body></html>"
        # Altura dinâmica: ~550px por cartão + 300px de header/padding
        altura_iframe = max(1200, len(df_mes) * 550 + 300)
        components.html(full_html, height=altura_iframe, scrolling=True)

    else:
        st.info(f"🗓️ Nenhum aniversariante cadastrado para {nome_mes_atual}.")
else:
    st.warning("⚠️ Nenhum dado encontrado no banco de dados.")
