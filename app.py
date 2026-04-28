import base64
import html as html_lib
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
from datetime import datetime
from utils import get_supabase, to_bool, cor_hex_valida, carregar_config

st.set_page_config(page_title="Mural de Aniversariantes", layout="wide", page_icon="🎉")

# ── CONSTANTES ───────────────────────────────────────────────────────────────
POSTIT_COLORS = [
    {"bg": "#fef08a", "text": "#3f6212", "shadow": "rgba(250,204,21,0.28)"},
    {"bg": "#bbf7d0", "text": "#14532d", "shadow": "rgba(34,197,94,0.22)"},
    {"bg": "#fed7aa", "text": "#7c2d12", "shadow": "rgba(249,115,22,0.22)"},
    {"bg": "#fecdd3", "text": "#881337", "shadow": "rgba(244,63,94,0.22)"},
    {"bg": "#bfdbfe", "text": "#1e3a5f", "shadow": "rgba(59,130,246,0.22)"},
    {"bg": "#e9d5ff", "text": "#4c1d95", "shadow": "rgba(139,92,246,0.22)"},
]

CONFETE_CORES = ["#f472b6", "#fbbf24", "#34d399", "#60a5fa", "#a78bfa", "#fb923c"]

MESES_PTBR = {
    1: "Janeiro",  2: "Fevereiro", 3: "Março",    4: "Abril",
    5: "Maio",     6: "Junho",     7: "Julho",     8: "Agosto",
    9: "Setembro", 10: "Outubro",  11: "Novembro", 12: "Dezembro",
}

# ── MODO TV ───────────────────────────────────────────────────────────────────
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

# ── CONEXÃO & CONFIG ──────────────────────────────────────────────────────────
supabase = get_supabase()
config   = carregar_config()

exibir_mural     = to_bool(config.get("exibir_mural",    False))
liberar_recados  = to_bool(config.get("liberar_recados", False))
liberar_cadastro = to_bool(config.get("liberar_cadastro", True))

# ── FUNÇÕES COM CACHE ─────────────────────────────────────────────────────────
# O prefixo _ nos parâmetros indica ao Streamlit que não deve tentar
# serializar/comparar esses argumentos para fins de cache (ex.: cliente Supabase).
@st.cache_data(ttl=120)
def carregar_aniversariantes(_supabase):
    return _supabase.table("aniversariantes").select("*").execute().data or []

@st.cache_data(ttl=120)
def carregar_recados(_supabase):
    return _supabase.table("recados").select("*").execute().data or []

# ── ADMIN ─────────────────────────────────────────────────────────────────────
st.sidebar.title("⚙️ Administração")
senha_digitada = st.sidebar.text_input("Acesso restrito", type="password")

# Senha lida do st.secrets — nunca hardcoded no código
SENHA_CORRETA = st.secrets.get("ADMIN_PASSWORD", "")
modo_admin    = bool(SENHA_CORRETA) and (senha_digitada == SENHA_CORRETA)

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

    config           = carregar_config()
    exibir_mural     = to_bool(config.get("exibir_mural",    False))
    liberar_recados  = to_bool(config.get("liberar_recados", False))
    liberar_cadastro = to_bool(config.get("liberar_cadastro", True))

    st.sidebar.divider()

    with st.sidebar.expander("🔐 Controlos de Acesso", expanded=True):
        novo_cadastro = st.checkbox("Libertar Aba de Cadastro", value=liberar_cadastro)
        novo_recados  = st.checkbox("Libertar Aba de Recados",  value=liberar_recados)
        novo_exibir   = st.checkbox("🎉 REVELAR MURAL FINAL",   value=exibir_mural)

    with st.sidebar.expander("🎨 Personalização Visual", expanded=False):
        cor_fundo_banco = config.get("cor_fundo")
        if cor_hex_valida(cor_fundo_banco):
            cor_fundo = st.color_picker("Cor base do Mural", value=cor_fundo_banco)
        else:
            cor_fundo = st.color_picker("Cor base do Mural")

        imagem_fundo = st.file_uploader("Imagem de Fundo", type=["jpg", "png", "jpeg"])

    img_b64_admin  = None
    img_tipo_admin = None
    if imagem_fundo is not None:
        img_bytes_admin = imagem_fundo.read()
        img_b64_admin   = base64.b64encode(img_bytes_admin).decode()
        img_tipo_admin  = imagem_fundo.type
        estilo_fundo = (
            f"background-image: url('data:{img_tipo_admin};base64,{img_b64_admin}'); "
            "background-size: cover; background-position: center top; background-repeat: no-repeat;"
        )
    else:
        estilo_fundo = f"background-color: {cor_fundo};"

    st.sidebar.write("")
    col_save, col_cache = st.sidebar.columns(2)

    if col_save.button("💾 Guardar", type="primary", use_container_width=True):
        atualizar_config("liberar_cadastro", novo_cadastro)
        atualizar_config("liberar_recados",  novo_recados)
        atualizar_config("exibir_mural",     novo_exibir)
        atualizar_config("cor_fundo",        cor_fundo)
        if img_b64_admin is not None:
            fundo_data_url = f"data:{img_tipo_admin};base64,{img_b64_admin}"
            atualizar_config("imagem_fundo", fundo_data_url)
        # Limpar cache para que os dados reflitam imediatamente após salvar
        carregar_aniversariantes.clear()
        carregar_recados.clear()
        config = carregar_config()
        st.sidebar.success("Atualizado!")
        st.rerun()

    if col_cache.button("🔄 Limpar Cache", use_container_width=True):
        carregar_aniversariantes.clear()
        carregar_recados.clear()
        st.sidebar.success("Cache limpo!")
        st.rerun()

elif senha_digitada != "":
    st.sidebar.error("Senha incorreta.")

# ── ESTILO DE FUNDO (não-admin) ───────────────────────────────────────────────
if not modo_admin:
    imagem_salva = config.get("imagem_fundo", "")
    cor_salva    = config.get("cor_fundo")
    if imagem_salva:
        estilo_fundo = (
            f"background-image: url('{imagem_salva}'); "
            "background-size: cover; background-position: center top; background-repeat: no-repeat;"
        )
    elif cor_hex_valida(cor_salva):
        estilo_fundo = f"background-color: {cor_salva};"
    else:
        estilo_fundo = ""

# ── PORTEIRO ──────────────────────────────────────────────────────────────────
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
            background: rgba(0,0,0,0.50);
            backdrop-filter: blur(14px);
            -webkit-backdrop-filter: blur(14px);
            border: 1px solid rgba(255,255,255,0.15);
            border-radius: 20px;
            padding: clamp(30px,5vw,60px) clamp(20px,4vw,50px);
            text-align: center;
            width: min(90vw,560px);
            margin: clamp(6vh,10vh,15vh) auto;
            box-shadow: 0 8px 40px 0 rgba(0,0,0,0.5);
            color: white;
            animation: fadeIn 1s ease-in-out;
        }}
        .emoji-animado {{
            font-size:5rem; display:inline-block;
            animation:pulse 2s infinite; margin-bottom:10px;
            filter:drop-shadow(0 4px 6px rgba(0,0,0,0.3));
        }}
        .porteiro-titulo {{
            font-family:'Playfair Display',serif; font-size:2.5rem;
            font-weight:700; margin-bottom:15px; text-shadow:0 2px 8px rgba(0,0,0,0.7);
        }}
        .porteiro-texto {{
            font-family:'Lato',sans-serif; font-size:1.1rem;
            line-height:1.6; color:#e2e8f0; text-shadow:0 1px 4px rgba(0,0,0,0.7);
        }}
        @keyframes pulse {{
            0%  {{ transform:scale(1); }}
            50% {{ transform:scale(1.15) rotate(-5deg); }}
            100%{{ transform:scale(1); }}
        }}
        @keyframes fadeIn {{
            from{{ opacity:0; transform:translateY(20px); }}
            to  {{ opacity:1; transform:translateY(0); }}
        }}
    </style>
    <div class="porteiro-card">
        <div class="emoji-animado">🤫</div>
        <div class="porteiro-titulo">Mural em Preparação</div>
        <div class="porteiro-texto">
            A equipa está a tratar de cada detalhe com muito carinho!<br><br>
            Fique atento às comunicações da GAFI para a grande revelação
            do nosso quadro de aniversariantes.
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# ── CARREGAMENTO DE DADOS ─────────────────────────────────────────────────────
dados      = []
df_recados = pd.DataFrame()

try:
    with st.spinner("A carregar aniversariantes..."):
        dados = carregar_aniversariantes(supabase)
    with st.spinner("A carregar recados..."):
        recados_raw = carregar_recados(supabase)
        if recados_raw:
            df_recados = pd.DataFrame(recados_raw).dropna(subset=["para_quem"])
except Exception as e:
    msg = str(e).lower()
    if any(k in msg for k in ("connection", "network", "timeout", "unreachable")):
        st.error("Sem ligação à base de dados. Verifique a sua internet e tente novamente.")
    else:
        st.error(f"Erro inesperado ao carregar os dados: {e}")

# ── MURAL ─────────────────────────────────────────────────────────────────────
hoje           = datetime.now()
mes_atual      = hoje.month
dia_atual      = hoje.day
nome_mes_atual = MESES_PTBR[mes_atual]

if dados:
    df = pd.DataFrame(dados)
    df["data_nascimento"] = pd.to_datetime(df["data_nascimento"], errors="coerce")
    df_mes = df[df["data_nascimento"].dt.month == mes_atual].copy()

    if not df_mes.empty:
        df_mes = df_mes.sort_values(by="data_nascimento")

        st.markdown("""
        <style>
            .block-container {
                padding-left: 1rem !important;
                padding-right: 1rem !important;
                padding-top: 1rem !important;
                max-width: 100% !important;
            }
            iframe[title="streamlit_components_v1.html"] {
                width: 100% !important;
                border: none !important;
            }
        </style>
        """, unsafe_allow_html=True)

        # ── Altura do iframe adaptativa ───────────────────────────────────────
        recados_por_pessoa = {}
        if not df_recados.empty and "para_quem" in df_recados.columns:
            recados_por_pessoa = df_recados["para_quem"].value_counts().to_dict()

        altura_iframe = 300  # reserva para o header
        for _, row in df_mes.iterrows():
            nome_r        = str(row.get("nome", ""))
            n_recados     = recados_por_pessoa.get(nome_r, 0)
            linhas_postit = max(1, (n_recados // 4) + 1)
            altura_iframe += 420 + linhas_postit * 170

        # ── HTML do mural ─────────────────────────────────────────────────────
        html_base = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <link rel="preconnect" href="https://fonts.googleapis.com">
            <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,700;0,900;1,700&family=Inter:wght@300;400;500;600;700&family=Caveat:wght@500;700&display=swap" rel="stylesheet">
            <style>
                *, *::before, *::after {{ margin:0; padding:0; box-sizing:border-box; }}

                html {{
                    {estilo_fundo}
                    background-attachment: fixed !important;
                    background-repeat: no-repeat !important;
                    background-size: cover !important;
                    background-position: center top !important;
                    min-height: 100%;
                }}
                body {{
                    background: transparent !important;
                    font-family: 'Inter', sans-serif;
                    color: #f8fafc;
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    padding: 36px 24px 72px;
                    min-height: 100vh;
                    width: 100%;
                }}

                /* ══ HEADER ══════════════════════════════════════════════════ */
                .mural-header {{
                    text-align: center; margin-bottom: 52px;
                    position: relative; width: 100%;
                    max-width: min(1400px, 96vw);
                    animation: fadeInDown 0.9s ease both;
                }}
                .mural-header-inner {{
                    background: rgba(255,255,255,0.18);
                    backdrop-filter: blur(22px); -webkit-backdrop-filter: blur(22px);
                    border: 1px solid rgba(255,255,255,0.35); border-radius: 20px;
                    padding: clamp(24px,4vw,32px) clamp(20px,5vw,70px) clamp(20px,3vw,28px);
                    width: min(600px, 92vw);
                    box-shadow: 0 16px 48px rgba(0,0,0,0.25), inset 0 1px 0 rgba(255,255,255,0.4);
                    display: inline-block; position: relative; overflow: hidden;
                }}
                .mural-header-inner::before {{
                    content:''; position:absolute; top:0; left:0; right:0; height:4px;
                    background: linear-gradient(90deg,#38bdf8,#818cf8,#f472b6);
                    border-radius: 20px 20px 0 0;
                }}
                .mural-header .subtitulo {{
                    font-family:'Inter',sans-serif; font-weight:600; font-size:0.78rem;
                    letter-spacing:8px; text-transform:uppercase; color:#ffffff;
                    text-shadow:0 1px 6px rgba(0,0,0,0.5); margin-bottom:8px;
                }}
                .mural-header h1 {{
                    font-family:'Playfair Display',serif;
                    font-size:clamp(2.1rem,4vw,3.8rem);
                    font-weight:900; color:#ffffff;
                    text-shadow:0 4px 20px rgba(0,0,0,0.6);
                    line-height:1.15; letter-spacing:-0.5px;
                }}
                .mural-header .mes-destaque {{
                    background:linear-gradient(100deg,#38bdf8 0%,#818cf8 50%,#f472b6 100%);
                    -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text;
                }}
                .header-deco {{
                    display:flex; justify-content:center; gap:10px; margin-top:14px;
                    opacity:0.6; font-size:1.2rem; letter-spacing:4px;
                }}

                /* ══ ANIMAÇÕES ═══════════════════════════════════════════════ */
                @keyframes fadeInDown {{
                    from{{ opacity:0; transform:translateY(-20px); }}
                    to  {{ opacity:1; transform:translateY(0); }}
                }}
                @keyframes fadeInUp {{
                    from{{ opacity:0; transform:translateY(40px); }}
                    to  {{ opacity:1; transform:translateY(0); }}
                }}
                @keyframes pulsoHoje {{
                    0%, 100% {{ box-shadow: 0 0 0 0 rgba(251,191,36,0.5), 0 12px 40px rgba(0,0,0,0.15); }}
                    50%       {{ box-shadow: 0 0 0 10px rgba(251,191,36,0), 0 20px 50px rgba(251,191,36,0.25); }}
                }}
                @keyframes confete {{
                    0%   {{ transform:translateY(-10px) rotate(0deg);   opacity:1; }}
                    100% {{ transform:translateY(80px)  rotate(720deg); opacity:0; }}
                }}
                @keyframes brilho {{
                    0%, 100% {{ opacity:0.65; }}
                    50%       {{ opacity:1; }}
                }}

                /* ══ GRID ════════════════════════════════════════════════════ */
                .mural-grid {{
                    display:flex; flex-direction:column; gap:28px;
                    max-width:min(1400px,96vw); width:100%;
                }}

                /* ══ CARD BASE ═══════════════════════════════════════════════ */
                .aniversariante-row {{
                    display: grid;
                    grid-template-columns: minmax(300px,1.2fr) 2fr;
                    gap: clamp(28px,4vw,56px);
                    background: rgba(255,255,255,0.65);
                    backdrop-filter: blur(18px); -webkit-backdrop-filter: blur(18px);
                    border: 1px solid rgba(255,255,255,0.6);
                    border-radius: 22px;
                    padding: clamp(30px,3.5vw,52px) clamp(28px,3.5vw,50px);
                    box-shadow: 0 12px 40px rgba(0,0,0,0.15);
                    animation: fadeInUp 0.7s ease both;
                    align-items: stretch;
                    min-height: 320px; position: relative; overflow: hidden;
                    transition: transform 0.3s ease, box-shadow 0.3s ease;
                }}
                .aniversariante-row::before {{
                    content:''; position:absolute; top:0; left:0; right:0; height:4px;
                    background: linear-gradient(90deg,#38bdf8,#818cf8,#f472b6);
                    border-radius: 20px 20px 0 0;
                }}
                .aniversariante-row:hover {{
                    transform: translateY(-3px);
                    box-shadow: 0 20px 50px rgba(0,0,0,0.25);
                }}

                /* ══ CARD "HOJE" — destaque dourado ══════════════════════════ */
                .aniversariante-row.hoje {{
                    border: 2px solid rgba(251,191,36,0.8);
                    background: rgba(255,251,235,0.78);
                    animation: fadeInUp 0.7s ease both, pulsoHoje 2.8s ease-in-out 0.8s infinite;
                }}
                .aniversariante-row.hoje::before {{
                    background: linear-gradient(90deg,#f59e0b,#fbbf24,#f472b6);
                }}
                .badge-hoje {{
                    display: inline-flex; align-items: center; gap: 5px;
                    background: linear-gradient(135deg,#f59e0b,#fbbf24);
                    color: #78350f; font-family:'Inter',sans-serif;
                    font-size:0.72rem; font-weight:800; letter-spacing:1.5px;
                    text-transform:uppercase; padding:5px 14px; border-radius:20px;
                    margin-top:8px; box-shadow:0 3px 10px rgba(245,158,11,0.4);
                    animation: brilho 1.8s ease-in-out infinite;
                }}

                /* ══ CONFETE ═════════════════════════════════════════════════ */
                .confete-wrapper {{
                    position:absolute; top:0; left:0; width:100%; height:100%;
                    pointer-events:none; overflow:hidden; border-radius:22px; z-index:0;
                }}
                .confete-piece {{
                    position:absolute; top:-20px; width:8px; height:8px;
                    border-radius:2px;
                    animation: confete 3s ease-in infinite;
                }}

                /* ══ POLAROID ════════════════════════════════════════════════ */
                .polaroid-container {{
                    width:100%; display:flex;
                    align-items:center; justify-content:center; padding:10px;
                    position:relative; z-index:1;
                }}
                .polaroid-wrapper {{
                    position:relative; width:100%; max-width:320px;
                    display:flex; justify-content:center;
                }}
                .polaroid-wrapper::before {{
                    content:''; position:absolute; inset:0;
                    background:rgba(0,0,0,0.08); border-radius:4px;
                    transform:rotate(4deg) translateY(6px); z-index:0;
                }}
                .polaroid {{
                    background:#ffffff; padding:16px 16px 58px; border-radius:4px;
                    box-shadow:0 16px 40px rgba(0,0,0,0.15),0 3px 10px rgba(0,0,0,0.1);
                    width:100%; color:#1e293b; text-align:center;
                    position:relative; z-index:1; transition:transform 0.45s ease;
                }}
                .polaroid::after {{
                    content:''; position:absolute; top:-14px; left:50%;
                    transform:translateX(-50%) rotate(-2deg); width:90px; height:28px;
                    background:linear-gradient(135deg,rgba(255,255,255,0.9),rgba(255,255,255,0.5));
                    backdrop-filter:blur(4px); box-shadow:0 2px 6px rgba(0,0,0,0.1);
                    border-radius:3px; z-index:5; border:1px solid rgba(0,0,0,0.05);
                }}
                .polaroid:hover {{ transform:scale(1.04) rotate(1deg); }}
                .foto {{
                    width:100%; aspect-ratio:1/1; background-size:cover;
                    background-position:center 20%;
                    border-radius:2px; border:1px solid #e2e8f0;
                    filter:contrast(1.02) brightness(1.02);
                }}
                .foto-placeholder {{
                    width:100%; aspect-ratio:1/1;
                    background:linear-gradient(135deg,#f1f5f9,#cbd5e1);
                    display:flex; align-items:center; justify-content:center;
                    font-size:4.5rem; border-radius:2px;
                }}
                .nome {{
                    font-family:'Playfair Display',serif;
                    font-size:clamp(1.1rem,1.8vw,1.6rem);
                    font-weight:900; margin-top:16px; color:#0f172a; line-height:1.2;
                    overflow:hidden; display:-webkit-box;
                    -webkit-line-clamp:2; -webkit-box-orient:vertical; word-break:break-word;
                }}
                .data-badge {{
                    display:inline-flex; align-items:center; gap:4px;
                    background:#f1f5f9; color:#0284c7;
                    font-family:'Inter',sans-serif; font-size:0.75rem; font-weight:700;
                    letter-spacing:1.2px; text-transform:uppercase;
                    padding:5px 14px; border-radius:20px;
                    margin-top:10px; border:1px solid #e2e8f0;
                }}
                .curiosidade-txt {{
                    font-size:0.8rem; color:#64748b; margin-top:12px;
                    font-style:italic; line-height:1.4;
                    border-top:1px dashed #cbd5e1; padding-top:10px;
                }}

                /* ══ RECADOS ═════════════════════════════════════════════════ */
                .recados-section {{
                    display:flex; flex-direction:column;
                    justify-content:flex-start; min-width:0;
                    position:relative; z-index:1;
                }}
                .recados-titulo {{
                    font-family:'Playfair Display',serif;
                    font-size:clamp(1.2rem,2vw,1.9rem);
                    font-weight:700; font-style:italic; color:#1e293b;
                    text-shadow:0 1px 3px rgba(255,255,255,0.6);
                    margin-bottom:18px; padding-bottom:12px;
                    border-bottom:1px solid rgba(0,0,0,0.1);
                    display:flex; justify-content:space-between;
                    align-items:center; gap:12px; flex-wrap:wrap;
                }}
                .recados-titulo-nome {{ color:#0284c7; }}
                .recados-titulo-emoji {{
                    font-size:1.7rem; font-style:normal;
                    flex-shrink:0; line-height:1; align-self:center;
                }}
                .badge-contagem {{
                    display:inline-flex; align-items:center; gap:4px;
                    background:linear-gradient(135deg,#0ea5e9,#38bdf8);
                    color:#fff; font-family:'Inter',sans-serif;
                    font-size:0.7rem; font-weight:700; letter-spacing:0.5px;
                    padding:3px 10px; border-radius:20px;
                    box-shadow:0 2px 8px rgba(14,165,233,0.35);
                    font-style:normal; flex-shrink:0;
                }}
                .area-post-it {{
                    display:flex; flex-wrap:wrap; gap:18px; align-content:flex-start;
                }}
                .post-it {{
                    padding:18px 15px 14px;
                    width:clamp(140px,18vw,175px); min-height:130px;
                    font-family:'Caveat',cursive; font-size:1.05rem;
                    border-radius:3px 16px 3px 3px;
                    display:flex; flex-direction:column;
                    justify-content:flex-start; gap:10px; position:relative;
                    transition:transform 0.28s ease, box-shadow 0.28s ease;
                }}
                .post-it::before {{
                    content:'📌'; position:absolute; top:-12px; left:50%;
                    transform:translateX(-50%); font-size:1.2rem;
                    filter:drop-shadow(0 2px 3px rgba(0,0,0,0.2));
                }}
                .post-it:hover {{
                    transform:scale(1.08) translateY(-4px) rotate(1deg) !important;
                    z-index:10;
                }}
                .post-it-msg {{
                    line-height:1.35; font-weight:700;
                    color:rgba(0,0,0,0.85); padding-top:4px; flex:1;
                    overflow:hidden; display:-webkit-box;
                    -webkit-line-clamp:5; -webkit-box-orient:vertical; word-break:break-word;
                }}
                .post-it-autor {{
                    font-size:0.88rem; font-weight:700; color:rgba(0,0,0,0.6);
                    text-align:right; margin-top:auto;
                    border-top:1px dashed rgba(0,0,0,0.15); padding-top:8px;
                    overflow:hidden; white-space:nowrap; text-overflow:ellipsis;
                }}
                .sem-recados {{
                    color:#475569; text-shadow:0 1px 3px rgba(255,255,255,0.6);
                    font-size:1.05rem; font-style:italic; padding:28px 0;
                    display:flex; align-items:center; gap:8px;
                }}

                /* ══ BOTÃO VOLTAR AO TOPO ════════════════════════════════════ */
                .btn-topo {{
                    position:fixed; bottom:30px; left:30px;
                    background:rgba(15,23,42,0.65);
                    backdrop-filter:blur(10px); -webkit-backdrop-filter:blur(10px);
                    border:1px solid rgba(255,255,255,0.2);
                    color:#fff; padding:10px 18px; border-radius:50px;
                    cursor:pointer; font-family:'Inter',sans-serif;
                    font-size:0.85rem; font-weight:600;
                    box-shadow:0 4px 14px rgba(0,0,0,0.3);
                    transition:all 0.25s ease;
                    display:none; align-items:center; gap:6px; z-index:1000;
                }}
                .btn-topo:hover {{
                    background:rgba(15,23,42,0.88); transform:translateY(-2px);
                }}
                .btn-topo.visivel {{ display:flex; }}

                /* ══ BOTÕES DE IMPRESSÃO ════════════════════════════════════ */
                .print-toolbar {{
                    position:fixed; bottom:30px; right:30px;
                    display:flex; flex-direction:column; gap:8px; z-index:1000;
                    background:rgba(15,23,42,0.55);
                    backdrop-filter:blur(10px); -webkit-backdrop-filter:blur(10px);
                    border:1px solid rgba(255,255,255,0.15);
                    border-radius:16px; padding:12px;
                }}
                .btn-imprimir {{
                    background:linear-gradient(135deg,#0ea5e9,#38bdf8);
                    color:#0f172a; border:none;
                    padding:13px 22px; border-radius:50px;
                    font-family:'Inter',sans-serif; font-size:0.9rem; font-weight:700;
                    box-shadow:0 8px 20px rgba(14,165,233,0.4),0 2px 6px rgba(0,0,0,0.3);
                    cursor:pointer; transition:all 0.28s ease;
                    display:flex; align-items:center; gap:8px;
                }}
                .btn-imprimir:hover {{
                    transform:translateY(-3px) scale(1.03);
                    box-shadow:0 14px 28px rgba(14,165,233,0.5);
                }}
                .btn-paisagem {{ background:linear-gradient(135deg,#6366f1,#818cf8); }}

                /* ══ IMPRESSÃO ═══════════════════════════════════════════════ */
                @media print {{
                    * {{ -webkit-print-color-adjust:exact !important; print-color-adjust:exact !important; }}
                    @page {{ size:A3 portrait; margin:0; }}
                    .btn-imprimir, .print-toolbar, .orientacao-badge,
                    .btn-topo {{ display:none !important; }}
                    html, body {{
                        {estilo_fundo}
                        background-size:cover !important;
                        background-position:center top !important;
                        background-repeat:no-repeat !important;
                        background-attachment:scroll !important;
                        margin:0 !important; padding:0 !important;
                    }}
                    .aniversariante-row {{
                        break-inside:avoid !important;
                        page-break-inside:avoid !important;
                        display:grid !important;
                        grid-template-columns:minmax(320px,1.2fr) 2fr !important;
                        animation:none !important;
                    }}
                    .confete-wrapper {{ display:none !important; }}
                }}

                @media (max-width:850px) {{
                    .aniversariante-row {{ grid-template-columns:1fr; padding:24px; }}
                }}
            </style>
            <style id="orientacao-style">
                @media print {{ @page {{ size:A3 portrait; margin:0; }} }}
            </style>
        </head>
        <body>
            <script>
                var IS_TV = {'true' if is_tv else 'false'};

                /* ── Orientação de impressão ── */
                function applyOrientation(ori) {{
                    document.getElementById('orientacao-style').textContent =
                        '@media print {{ @page {{ size:A3 ' + ori + '; margin:0; }} }}';
                    var badge = document.getElementById('badge-orientacao');
                    badge.textContent = ori === 'landscape' ? '↔ PAISAGEM A3' : '↕ RETRATO A3';
                    badge.style.display = 'block';
                }}
                function imprimirCom(ori) {{
                    applyOrientation(ori);
                    setTimeout(function(){{ window.print(); }}, 100);
                }}

                /* ── Botão Voltar ao Topo ── */
                window.addEventListener('scroll', function() {{
                    var btn = document.getElementById('btn-topo');
                    if (!btn) return;
                    btn.classList.toggle('visivel', window.scrollY > 320);
                }}, {{ passive: true }});

                function voltarTopo() {{
                    window.scrollTo({{ top: 0, behavior: 'smooth' }});
                }}

                document.addEventListener('DOMContentLoaded', function() {{
                    applyOrientation('portrait');
                    if (IS_TV) {{
                        var toolbar = document.querySelector('.print-toolbar');
                        var badge   = document.getElementById('badge-orientacao');
                        var topo    = document.getElementById('btn-topo');
                        if (toolbar) toolbar.style.display = 'none';
                        if (badge)   badge.style.display   = 'none';
                        if (topo)    topo.style.display     = 'none';
                    }}
                }});
            </script>

            <div id="badge-orientacao" class="orientacao-badge"></div>

            <button id="btn-topo" class="btn-topo" onclick="voltarTopo()">↑ Topo</button>

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
            # Escapar dados do utilizador (XSS)
            nome              = html_lib.escape(str(row.get("nome", "Sem nome")).strip())
            texto_curiosidade = html_lib.escape(str(row.get("curiosidade", "")).strip())
            dia = row["data_nascimento"].day if pd.notna(row["data_nascimento"]) else "?"

            # Primeiro nome seguro
            partes        = nome.split()
            primeiro_nome = partes[0] if partes else nome

            # URL da foto — escapar aspas simples
            img_url = str(row.get("foto_url", "")).strip().replace("'", "%27")
            if img_url:
                foto_html = f'<div class="foto" style="background-image:url(\'{img_url}\');"></div>'
            else:
                foto_html = '<div class="foto-placeholder">👤</div>'

            curiosidade_html = ""
            if texto_curiosidade:
                curiosidade_html = f'<div class="curiosidade-txt">"{texto_curiosidade}"</div>'

            # Verificar se é aniversário hoje
            e_hoje     = (dia == dia_atual)
            classe_row = "aniversariante-row hoje" if e_hoje else "aniversariante-row"
            badge_hoje = '<div class="badge-hoje">🎂 Hoje é o grande dia!</div>' if e_hoje else ""

            # Confete animado apenas para aniversariante do dia
            confete_html = ""
            if e_hoje:
                pecas = ""
                for ci in range(14):
                    cor   = CONFETE_CORES[ci % len(CONFETE_CORES)]
                    left  = (ci * 7) % 100
                    delay = round((ci * 0.22) % 3, 2)
                    dur   = round(2.5 + (ci % 3) * 0.5, 1)
                    pecas += (
                        f'<div class="confete-piece" '
                        f'style="left:{left}%;background:{cor};'
                        f'animation-duration:{dur}s;animation-delay:{delay}s;"></div>'
                    )
                confete_html = f'<div class="confete-wrapper">{pecas}</div>'

            # Recados
            n_recados_pessoa = 0
            post_its_html    = ""
            if not df_recados.empty and "para_quem" in df_recados.columns:
                # Comparar com o nome original (não escapado) para bater com o banco
                nome_original    = str(row.get("nome", "")).strip()
                recados_pessoa   = df_recados[df_recados["para_quem"] == nome_original]
                n_recados_pessoa = len(recados_pessoa)

                if recados_pessoa.empty:
                    post_its_html = '<p class="sem-recados">📌 Seja o primeiro a deixar um recado!</p>'
                else:
                    for i, (_, recado) in enumerate(recados_pessoa.iterrows()):
                        mensagem = html_lib.escape(str(recado.get("mensagem", "")).strip())
                        autor    = html_lib.escape(str(recado.get("de_quem", "Anônimo")).strip())

                        # Rotação determinista — nunca muda entre reruns
                        seed_val = hash(mensagem + autor + nome) & 0xFFFFFF
                        rotacao  = (seed_val % 9) - 4

                        cor = POSTIT_COLORS[i % len(POSTIT_COLORS)]

                        post_its_html += f"""
                        <div class="post-it"
                             style="background-color:{cor['bg']};
                                    transform:rotate({rotacao}deg);
                                    box-shadow:4px 6px 15px {cor['shadow']},0 1px 3px rgba(0,0,0,0.06);">
                            <div class="post-it-msg">{mensagem}</div>
                            <div class="post-it-autor">~ {autor}</div>
                        </div>
                        """
            else:
                post_its_html = '<p class="sem-recados">📌 Seja o primeiro a deixar um recado!</p>'

            # Badge de contagem de recados
            badge_contagem = ""
            if n_recados_pessoa > 0:
                label = "recado" if n_recados_pessoa == 1 else "recados"
                badge_contagem = (
                    f'<span class="badge-contagem">💬 {n_recados_pessoa} {label}</span>'
                )

            # Delay máximo 0.6s para não atrasar murais com muitos cards
            delay = min(idx * 0.15, 0.6)

            cartoes_html += f"""
            <div class="{classe_row}" style="animation-delay:{delay}s;">
                {confete_html}
                <div class="polaroid-container">
                    <div class="polaroid-wrapper">
                        <div class="polaroid">
                            {foto_html}
                            <div class="nome">{nome}</div>
                            <div class="data-badge">🎉 {dia} de {nome_mes_atual}</div>
                            {badge_hoje}
                            {curiosidade_html}
                        </div>
                    </div>
                </div>
                <div class="recados-section">
                    <div class="recados-titulo">
                        <span>
                            Mensagens para
                            <span class="recados-titulo-nome">{primeiro_nome}</span>
                            {badge_contagem}
                        </span>
                        <span class="recados-titulo-emoji">🎂</span>
                    </div>
                    <div class="area-post-it">
                        {post_its_html}
                    </div>
                </div>
            </div>
            """

        full_html = html_base + cartoes_html + "</div></body></html>"
        components.html(full_html, height=altura_iframe, scrolling=True)

    else:
        # ── Estado vazio estilizado dentro do iframe ──────────────────────────
        empty_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=Inter:wght@400;500&display=swap" rel="stylesheet">
            <style>
                *, *::before, *::after {{ margin:0; padding:0; box-sizing:border-box; }}
                html {{
                    {estilo_fundo}
                    background-size:cover; background-position:center top;
                    background-repeat:no-repeat; min-height:100%;
                }}
                body {{
                    background:transparent; display:flex;
                    align-items:center; justify-content:center;
                    min-height:100vh; font-family:'Inter',sans-serif;
                }}
                @keyframes fadeInUp {{
                    from{{ opacity:0; transform:translateY(30px); }}
                    to  {{ opacity:1; transform:translateY(0); }}
                }}
                .empty-state {{
                    text-align:center;
                    background:rgba(255,255,255,0.65);
                    backdrop-filter:blur(18px); -webkit-backdrop-filter:blur(18px);
                    border:1px solid rgba(255,255,255,0.6);
                    border-radius:22px; padding:72px 48px;
                    max-width:520px;
                    box-shadow:0 12px 40px rgba(0,0,0,0.12);
                    animation:fadeInUp 0.7s ease both;
                }}
                .empty-emoji {{ font-size:4rem; margin-bottom:20px; }}
                .empty-titulo {{
                    font-family:'Playfair Display',serif; font-size:1.8rem;
                    font-weight:700; color:#1e293b; margin-bottom:12px;
                }}
                .empty-texto {{
                    font-size:1.05rem; color:#64748b; line-height:1.6;
                }}
            </style>
        </head>
        <body>
            <div class="empty-state">
                <div class="empty-emoji">🗓️</div>
                <div class="empty-titulo">Nenhum aniversariante em {nome_mes_atual}</div>
                <div class="empty-texto">
                    Não há celebrações registadas para este mês.<br>
                    Aproveite para cadastrar novos colaboradores!
                </div>
            </div>
        </body>
        </html>
        """
        components.html(empty_html, height=420, scrolling=False)

else:
    st.warning("⚠️ Nenhum dado encontrado no banco de dados.")
