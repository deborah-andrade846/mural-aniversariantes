import base64
import html as html_lib
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
from datetime import datetime
from utils import get_supabase, to_bool, cor_hex_valida, carregar_config
from streamlit_autorefresh import st_autorefresh

# ── CONSTANTE: tamanho máximo de imagem de fundo (2 MB) ──────────────────────
MAX_IMG_BYTES = 2 * 1024 * 1024

st.set_page_config(page_title="Mural de Aniversariantes", layout="wide", page_icon="🎉")

# ── CONSTANTES ───────────────────────────────────────────────────────────────
POSTIT_COLORS = [
    {"bg": "#f8fafc", "text": "#334155", "shadow": "rgba(148,163,184,0.2)"},
    {"bg": "#e2e8f0", "text": "#1e293b", "shadow": "rgba(100,116,139,0.15)"},
    {"bg": "#f1f5f9", "text": "#0f172a", "shadow": "rgba(71,85,105,0.15)"},
    {"bg": "#e2e8f0", "text": "#1e293b", "shadow": "rgba(100,116,139,0.15)"},
    {"bg": "#f8fafc", "text": "#334155", "shadow": "rgba(148,163,184,0.2)"},
    {"bg": "#e2e8f0", "text": "#1e293b", "shadow": "rgba(100,116,139,0.15)"},
]

CONFETE_CORES = ["#fbbf24", "#38bdf8", "#34d399", "#818cf8", "#f472b6", "#fb923c"]

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

# ── AUTO‑REFRESH ESTRUTURADO (a cada 1 hora) ─────────────────────────────────
st_autorefresh(interval=3600 * 1000, limit=None, key="global_autorefresh")

# ── CONEXÃO & CONFIG ──────────────────────────────────────────────────────────
supabase = get_supabase()
config   = carregar_config()

exibir_mural     = to_bool(config.get("exibir_mural",    False))
liberar_recados  = to_bool(config.get("liberar_recados", False))
liberar_cadastro = to_bool(config.get("liberar_cadastro", True))

# ── FUNÇÕES COM CACHE (TTL de 1 hora) ───────────────────────────────────────
@st.cache_data(ttl=3600)
def carregar_aniversariantes(_supabase):
    try:
        return _supabase.table("aniversariantes").select("*").execute().data or []
    except Exception:
        return None

@st.cache_data(ttl=3600)
def carregar_recados(_supabase):
    try:
        return _supabase.table("recados").select("*").execute().data or []
    except Exception:
        return None

# ── ADMIN ─────────────────────────────────────────────────────────────────────
st.sidebar.title("⚙️ Administração")
senha_digitada = st.sidebar.text_input("Acesso restrito", type="password")

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
        if len(img_bytes_admin) > MAX_IMG_BYTES:
            st.sidebar.error(
                f"⚠️ Imagem demasiado grande "
                f"({len(img_bytes_admin)/1024/1024:.1f} MB). "
                f"Máximo permitido: 2 MB."
            )
        else:
            img_b64_admin  = base64.b64encode(img_bytes_admin).decode()
            img_tipo_admin = imagem_fundo.type
            estilo_fundo   = (
                f"background-image: url('data:{img_tipo_admin};base64,{img_b64_admin}'); "
                "background-size: cover; background-position: center top; background-repeat: no-repeat;"
            )

    if img_b64_admin is None:
        estilo_fundo = f"background-color: {cor_fundo};"

    st.sidebar.divider()
    with st.sidebar.expander("📊 Estado actual do Mural", expanded=False):
        try:
            todos   = carregar_aniversariantes(supabase)
            df_prev = pd.DataFrame(todos) if todos else pd.DataFrame()
            if not df_prev.empty and "data_nascimento" in df_prev.columns:
                df_prev["data_nascimento"] = pd.to_datetime(df_prev["data_nascimento"], errors="coerce")
                n_mes = int((df_prev["data_nascimento"].dt.month == datetime.now().month).sum())
                n_total = len(df_prev)
                st.metric("Aniversariantes este mês", n_mes)
                st.metric("Total cadastrados", n_total)
                todos_recados = carregar_recados(supabase)
                st.metric("Total de recados", len(todos_recados) if todos_recados else 0)
            else:
                st.info("Sem dados disponíveis.")
        except Exception:
            st.warning("Não foi possível carregar estatísticas.")

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
            background: rgba(15,23,42,0.75);
            backdrop-filter: blur(14px);
            -webkit-backdrop-filter: blur(14px);
            border: 1px solid rgba(255,255,255,0.15);
            border-radius: 20px;
            padding: clamp(30px,5vw,60px) clamp(20px,4vw,50px);
            text-align: center;
            width: min(90vw,560px);
            margin: clamp(6vh,10vh,15vh) auto;
            box-shadow: 0 8px 32px rgba(0,0,0,0.3);
            color: #f1f5f9;
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
            font-family:'Inter',sans-serif; font-size:1.1rem;
            line-height:1.6; color:#cbd5e1; text-shadow:0 1px 4px rgba(0,0,0,0.7);
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
        raw_ani = carregar_aniversariantes(supabase)
        if raw_ani is None:
            raise ConnectionError("Falha na conexão com o Supabase.")
        dados = raw_ani
    with st.spinner("A carregar recados..."):
        recados_raw = carregar_recados(supabase)
        if recados_raw is None:
            raise ConnectionError("Falha na conexão com o Supabase.")
        if recados_raw:
            df_recados = pd.DataFrame(recados_raw).dropna(subset=["para_quem"])
except Exception as e:
    msg = str(e).lower()
    if any(k in msg for k in ("connection", "network", "timeout", "unreachable", "falha")):
        st.error("⚠️ Sem ligação à base de dados. Por favor, verifique a sua conexão de rede e tente novamente mais tarde.")
    else:
        st.error(f"⚠️ Erro inesperado ao carregar os dados: {e}")
    st.stop()

if not dados:
    st.warning("📭 Nenhum aniversariante encontrado no banco de dados. Cadastre os colaboradores para começar!")
    st.stop()

# ── MURAL ─────────────────────────────────────────────────────────────────────
hoje           = datetime.now()
mes_atual      = hoje.month
dia_atual      = hoje.day
nome_mes_atual = MESES_PTBR[mes_atual]

df = pd.DataFrame(dados)
df["data_nascimento"] = pd.to_datetime(df["data_nascimento"], errors="coerce")
df_mes = df[df["data_nascimento"].dt.month == mes_atual].copy()

if df_mes.empty:
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
                background: rgba(255,255,255,0.85);
                backdrop-filter:blur(12px);
                border:1px solid rgba(0,0,0,0.05);
                border-radius:22px; padding:72px 48px;
                max-width:520px;
                box-shadow:0 12px 40px rgba(0,0,0,0.08);
                animation:fadeInUp 0.7s ease both;
            }}
            .empty-emoji {{ font-size:4rem; margin-bottom:20px; }}
            .empty-titulo {{
                font-family:'Playfair Display',serif; font-size:1.8rem;
                font-weight:700; color:#1e293b; margin-bottom:12px;
            }}
            .empty-texto {{
                font-size:1.05rem; color:#475569; line-height:1.6;
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
    st.stop()

df_mes = df_mes.sort_values(
    by="data_nascimento",
    key=lambda s: s.dt.day.apply(lambda d: (0 if d == dia_atual else 1, d))
)

total_mes = len(df_mes)

recados_por_pessoa = {}
if not df_recados.empty and "para_quem" in df_recados.columns:
    recados_por_pessoa = df_recados["para_quem"].value_counts().to_dict()

# ── CONSTRUÇÃO DOS CARDS (HTML) ──────────────────────────────────────────────
cartoes_html = ""

for idx, (_, row) in enumerate(df_mes.iterrows()):
    nome_raw = str(row.get("nome", "Sem nome")).strip()
    nome_formatado = nome_raw.title()
    nome           = html_lib.escape(nome_formatado)
    texto_curiosidade = html_lib.escape(str(row.get("curiosidade", "")).strip())
    dia = row["data_nascimento"].day if pd.notna(row["data_nascimento"]) else "?"

    partes        = nome_formatado.split()
    primeiro_nome = partes[0] if partes else nome_formatado

    img_url = str(row.get("foto_url", "")).strip().replace("'", "%27").replace('"', "%22")
    if img_url:
        foto_html = f'''
        <div class="foto-wrapper">
            <img class="foto-img" src="{img_url}"
                 onerror="this.style.display='none';this.nextElementSibling.style.display='flex';"
                 alt="Foto de {nome}" />
            <div class="foto-placeholder" style="display:none;">👤</div>
        </div>'''
    else:
        foto_html = '<div class="foto-wrapper"><div class="foto-placeholder">👤</div></div>'

    curiosidade_html = ""
    if texto_curiosidade:
        curiosidade_html = f'<div class="curiosidade-txt">"{texto_curiosidade}"</div>'

    e_hoje     = (dia == dia_atual)
    classe_row = "aniversariante-row hoje" if e_hoje else "aniversariante-row"
    badge_hoje = '<div class="badge-hoje">🎂 Hoje é o grande dia!</div>' if e_hoje else ""

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

    n_recados_pessoa = 0
    post_its_html    = ""

    if not liberar_recados:
        post_its_html = """
        <p class="sem-recados sem-recados-bloqueado">
            🔒 Os recados serão revelados em breve!
        </p>"""
    elif not df_recados.empty and "para_quem" in df_recados.columns:
        nome_original    = nome_raw
        recados_pessoa   = df_recados[df_recados["para_quem"] == nome_original]
        n_recados_pessoa = len(recados_pessoa)

        if recados_pessoa.empty:
            post_its_html = '<p class="sem-recados">📌 Seja o primeiro a deixar um recado!</p>'
        else:
            for i, (_, recado) in enumerate(recados_pessoa.iterrows()):
                mensagem = html_lib.escape(str(recado.get("mensagem", "")).strip())
                autor_raw = str(recado.get("de_quem", "Anônimo")).strip()
                autor = html_lib.escape(autor_raw.title()) if autor_raw else "Anônimo"
                seed_val = hash(mensagem + autor + nome) & 0xFFFFFF
                rotacao  = (seed_val % 5) - 2
                cor = POSTIT_COLORS[i % len(POSTIT_COLORS)]
                post_its_html += f"""
                <div class="post-it"
                     style="background-color:{cor['bg']};
                            transform:rotate({rotacao}deg);
                            box-shadow:4px 6px 12px {cor['shadow']},0 1px 3px rgba(0,0,0,0.04);">
                    <div class="post-it-msg">{mensagem}</div>
                    <div class="post-it-autor">~ {autor}</div>
                </div>
                """
    else:
        post_its_html = '<p class="sem-recados">📌 Seja o primeiro a deixar um recado!</p>'

    badge_contagem = ""
    if n_recados_pessoa > 0:
        label = "recado" if n_recados_pessoa == 1 else "recados"
        badge_contagem = f'<span class="badge-contagem">💬 {n_recados_pessoa} {label}</span>'

    delay = min(idx * 0.12, 0.6)

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

# ── BASE DO HTML COMUM (estilos corporativos) ─────────────────────────────────
base_styles = f"""
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
        color: #1e293b;
        display: flex;
        flex-direction: column;
        align-items: center;
        padding: 36px 24px 72px;
        min-height: 100vh;
        width: 100%;
    }}

    .mural-header {{
        text-align: center; margin-bottom: 52px;
        width: 100%;
        max-width: min(1400px, 96vw);
        animation: fadeInDown 0.9s ease both;
    }}
    .mural-header-inner {{
        background: rgba(15,23,42,0.75);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(255,255,255,0.2);
        border-radius: 16px;
        padding: clamp(20px,3vw,32px) clamp(20px,4vw,50px);
        width: fit-content;
        max-width: min(800px, 90vw);
        box-shadow: 0 8px 32px rgba(0,0,0,0.3);
        display: inline-block;
        margin: 0 auto;
    }}
    .mural-header .subtitulo {{
        font-family:'Inter',sans-serif; font-weight:600; font-size:0.75rem;
        letter-spacing:6px; text-transform:uppercase; color:#94a3b8;
        margin-bottom:6px;
    }}
    .mural-header h1 {{
        font-family:'Playfair Display',serif;
        font-size:clamp(2.1rem,4vw,3.8rem);
        font-weight:900; color:#ffffff;
        text-shadow:0 4px 12px rgba(0,0,0,0.5);
        line-height:1.15;
    }}
    .header-deco {{
        display:flex; justify-content:center; gap:10px; margin-top:10px;
        opacity:0.6; font-size:1.2rem; letter-spacing:4px;
    }}
    .header-count {{
        margin-top:10px;
        font-size:0.8rem; font-weight:600;
        color:rgba(255,255,255,0.8);
        background:rgba(255,255,255,0.15);
        border-radius:20px; display:inline-block;
        padding:4px 16px;
    }}

    @keyframes fadeInDown {{
        from{{ opacity:0; transform:translateY(-20px); }}
        to  {{ opacity:1; transform:translateY(0); }}
    }}
    @keyframes fadeInUp {{
        from{{ opacity:0; transform:translateY(40px); }}
        to  {{ opacity:1; transform:translateY(0); }}
    }}

    .mural-grid {{
        display:flex; flex-direction:column; gap:28px;
        max-width:min(1400px,96vw); width:100%;
    }}

    .aniversariante-row {{
        display: grid;
        grid-template-columns: minmax(300px,1.2fr) 2fr;
        gap: clamp(28px,4vw,56px);
        background: rgba(255,255,255,0.9);
        backdrop-filter: blur(8px);
        border: 1px solid rgba(0,0,0,0.05);
        border-radius: 16px;
        padding: clamp(30px,3.5vw,52px) clamp(28px,3.5vw,50px);
        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        animation: fadeInUp 0.7s ease both;
        align-items: stretch;
        min-height: 320px; position: relative; overflow: hidden;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }}
    .aniversariante-row:hover {{
        transform: translateY(-2px);
        box-shadow: 0 12px 32px rgba(0,0,0,0.12);
    }}
    .aniversariante-row.hoje {{
        border: 2px solid #f59e0b;
        box-shadow: 0 4px 20px rgba(245,158,11,0.25);
    }}
    .badge-hoje {{
        display: inline-flex; align-items: center; gap: 4px;
        background: #fef3c7; color: #92400e;
        font-weight:700; font-size:0.7rem; letter-spacing:1px;
        padding:3px 12px; border-radius:20px; margin-top:8px;
    }}

    .confete-wrapper {{
        position:absolute; top:0; left:0; width:100%; height:100%;
        pointer-events:none; overflow:hidden; border-radius:16px; z-index:0;
    }}
    .confete-piece {{
        position:absolute; top:-20px; width:8px; height:8px;
        border-radius:2px;
        animation: confete 3s ease-in infinite;
    }}
    @keyframes confete {{
        0%   {{ transform:translateY(-10px) rotate(0deg);   opacity:1; }}
        100% {{ transform:translateY(80px)  rotate(720deg); opacity:0; }}
    }}

    .polaroid-container {{ width:100%; display:flex; align-items:center; justify-content:center; padding:10px; z-index:1; }}
    .polaroid-wrapper {{ position:relative; width:100%; max-width:320px; }}
    .polaroid {{
        background:#fff; padding:16px 16px 58px; border-radius:4px;
        box-shadow:0 8px 24px rgba(0,0,0,0.08);
        color:#1e293b; text-align:center; position:relative; z-index:1;
        transition:transform 0.3s ease;
    }}
    .polaroid:hover {{ transform:scale(1.02); }}
    .foto-wrapper {{ width:100%; aspect-ratio:1; border-radius:2px; overflow:hidden; }}
    .foto-img {{ width:100%; height:100%; object-fit:cover; display:block; }}
    .foto-placeholder {{
        width:100%; height:100%; background:#e2e8f0;
        display:flex; align-items:center; justify-content:center; font-size:3rem;
    }}
    .nome {{
        font-family:'Playfair Display',serif;
        font-size:clamp(1.1rem,1.8vw,1.6rem);
        font-weight:900; margin-top:12px; color:#0f172a; line-height:1.2;
        word-break:break-word;
    }}
    .data-badge {{
        display:inline-flex; align-items:center; gap:4px;
        background:#f1f5f9; color:#0284c7;
        font-weight:700; font-size:0.75rem; letter-spacing:1px;
        padding:3px 12px; border-radius:20px; margin-top:8px;
    }}
    .curiosidade-txt {{
        font-size:0.8rem; color:#475569; margin-top:10px;
        font-style:italic; border-top:1px dashed #cbd5e1; padding-top:8px;
    }}

    .recados-section {{ display:flex; flex-direction:column; justify-content:flex-start; min-width:0; z-index:1; }}
    .recados-titulo {{
        font-family:'Playfair Display',serif;
        font-size:clamp(1.2rem,2vw,1.9rem);
        font-weight:700; font-style:italic; color:#1e293b;
        margin-bottom:18px; padding-bottom:12px;
        border-bottom:1px solid #e2e8f0;
        display:flex; justify-content:space-between;
        align-items:center; gap:12px; flex-wrap:wrap;
    }}
    .recados-titulo-nome {{ color:#0284c7; }}
    .badge-contagem {{
        background:#0ea5e9; color:#fff; font-size:0.65rem; font-weight:700;
        padding:2px 10px; border-radius:20px; margin-left:6px;
    }}
    .area-post-it {{ display:flex; flex-wrap:wrap; gap:18px; align-content:flex-start; }}
    .post-it {{
        padding:18px 15px 14px;
        width:clamp(140px,18vw,175px); min-height:130px;
        font-family:'Caveat',cursive;
        border-radius:3px 16px 3px 3px;
        display:flex; flex-direction:column;
        justify-content:flex-start; gap:10px; position:relative;
        transition:transform 0.28s ease, box-shadow 0.28s ease;
    }}
    .post-it:hover {{
        transform:scale(1.05) translateY(-3px);
        box-shadow:0 12px 24px rgba(0,0,0,0.12) !important;
    }}
    .post-it-msg {{
        font-size:1.2rem; line-height:1.4; font-weight:700;
        color:#1e293b; overflow:hidden;
        display:-webkit-box; -webkit-line-clamp:5; -webkit-box-orient:vertical;
        word-break:break-word;
    }}
    .post-it-autor {{
        font-size:0.95rem; color:#64748b; text-align:right;
        margin-top:auto; border-top:1px dashed rgba(0,0,0,0.1); padding-top:8px;
        overflow:hidden; white-space:nowrap; text-overflow:ellipsis;
    }}
    .sem-recados {{
        color:#64748b; font-size:1.05rem; font-style:italic; padding:28px 0;
    }}
    .sem-recados-bloqueado {{
        background:rgba(100,116,139,0.06);
        border:1px dashed rgba(100,116,139,0.25);
        border-radius:10px; padding:16px 20px;
        color:#475569; font-weight:600;
    }}

    /* Botão Voltar ao Topo */
    .btn-topo {{
        position:fixed; bottom:30px; left:30px;
        background:rgba(15,23,42,0.75);
        backdrop-filter:blur(10px);
        border:1px solid rgba(255,255,255,0.2);
        color:#fff; padding:10px 18px; border-radius:50px;
        cursor:pointer; font-family:'Inter',sans-serif;
        font-size:0.85rem; font-weight:600;
        box-shadow:0 4px 14px rgba(0,0,0,0.3);
        transition:all 0.25s ease;
        display:none; align-items:center; gap:6px; z-index:1000;
    }}
    .btn-topo:hover {{
        background:rgba(15,23,42,0.9); transform:translateY(-2px);
    }}
    .btn-topo.visivel {{ display:flex; }}

    /* Barra de Impressão */
    .print-toolbar {{
        position:fixed; bottom:30px; right:30px;
        display:flex; flex-direction:column; gap:8px; z-index:1000;
        background:rgba(15,23,42,0.55);
        backdrop-filter:blur(10px);
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

    .orientacao-badge {{
        display:none;
        position:fixed; top:20px; right:20px;
        background:rgba(15,23,42,0.7); color:#f1f5f9;
        padding:6px 16px; border-radius:20px;
        font-family:'Inter',sans-serif; font-size:0.8rem; z-index:2000;
    }}

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

    .print-data-evento-header {{
        display: none;
    }}
    @media print {{
        .print-data-evento-header {{
            display: block;
            font-family: 'Playfair Display', serif;
            font-size: 1.4rem;
            font-weight: 700;
            color: #0f172a;
            text-align: center;
            margin-top: 0.8rem;
            padding: 0.5rem 1rem;
            border-top: 1px solid rgba(0,0,0,0.15);
            border-bottom: 1px solid rgba(0,0,0,0.15);
            background: rgba(255,255,255,0.3);
        }}
    }}
"""

# ── MODO TV: CARROSSEL AUTOMÁTICO ────────────────────────────────────────────
if is_tv:
    carousel_js = """
    <script>
        var slides = document.querySelectorAll('.aniversariante-row');
        var current = 0;
        function showSlide(index) {
            slides.forEach(function(slide, i) {
                slide.style.display = (i === index) ? 'grid' : 'none';
            });
        }
        if (slides.length > 0) {
            showSlide(0);
            setInterval(function() {
                current = (current + 1) % slides.length;
                showSlide(current);
            }, 7000);
        }
    </script>
    """
    carousel_style = """
    <style>
        .aniversariante-row { display: none; }
        .carousel-container {
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 80vh;
            padding: 2rem;
        }
    </style>
    """
    full_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,700;0,900;1,700&family=Inter:wght@300;400;500;600;700&family=Caveat:wght@500;700&display=swap" rel="stylesheet">
        <style>{base_styles}</style>
        {carousel_style}
    </head>
    <body>
        <div class="mural-header">
            <div class="mural-header-inner">
                <p class="subtitulo">✦ Celebrações GAFI ✦</p>
                <h1>Aniversariantes de <span style="color:#38bdf8;">{nome_mes_atual}</span></h1>
                <div class="header-deco">🎉 🎂 🎈</div>
                <div class="header-count">
                    {'🎂 1 aniversariante' if total_mes == 1 else f'🎂 {total_mes} aniversariantes'}
                    {' — incluindo hoje! 🥳' if any(df_mes["data_nascimento"].dt.day == dia_atual) else ''}
                </div>
            </div>
        </div>
        <div class="print-data-evento-header">Data do Evento: 30/04/2026</div>
        <div class="carousel-container">
            {cartoes_html}
        </div>
        <div class="orientacao-badge" id="badge-orientacao"></div>
        <button id="btn-topo" class="btn-topo" onclick="voltarTopo()">↑ Topo</button>
        <div class="print-toolbar">
            <button class="btn-imprimir" onclick="imprimirCom('portrait')">🖨️ Imprimir A3 — Retrato</button>
            <button class="btn-imprimir btn-paisagem" onclick="imprimirCom('landscape')">🖨️ Imprimir A3 — Paisagem</button>
        </div>
        <script>
            var IS_TV = true;

            function applyOrientation(ori) {{
                var style = document.createElement('style');
                style.textContent = '@media print {{ @page {{ size:A3 ' + ori + '; margin:0; }} }}';
                document.head.appendChild(style);
                var badge = document.getElementById('badge-orientacao');
                badge.textContent = ori === 'landscape' ? '↔ PAISAGEM A3' : '↕ RETRATO A3';
                badge.style.display = 'block';
            }}
            function imprimirCom(ori) {{
                applyOrientation(ori);
                setTimeout(function(){{ window.print(); }}, 100);
            }}

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
                var toolbar = document.querySelector('.print-toolbar');
                var badge   = document.getElementById('badge-orientacao');
                var topo    = document.getElementById('btn-topo');
                if (toolbar) toolbar.style.display = 'none';
                if (badge)   badge.style.display   = 'none';
                if (topo)    topo.style.display     = 'none';
                
                setTimeout(function() {{
                    try {{ window.parent.location.reload(); }}
                    catch(e) {{ window.location.reload(); }}
                }}, 300000);
            }});
        </script>
        {carousel_js}
    </body>
    </html>
    """
    components.html(full_html, height=700, scrolling=False)

else:
    # ── MURAL COMPLETO (desktop) ──────────────────────────────────────────
    altura_iframe = 400
    for _, row in df_mes.iterrows():
        nome_r = str(row.get("nome", ""))
        n_rec = recados_por_pessoa.get(nome_r, 0)
        linhas_postit = max(1, (n_rec // 4) + 1)
        altura_iframe += 380 + linhas_postit * 160

    full_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,700;0,900;1,700&family=Inter:wght@300;400;500;600;700&family=Caveat:wght@500;700&display=swap" rel="stylesheet">
        <style>{base_styles}</style>
        <style id="orientacao-style">
            @media print {{ @page {{ size:A3 portrait; margin:0; }} }}
        </style>
    </head>
    <body>
        <div class="mural-header">
            <div class="mural-header-inner">
                <p class="subtitulo">✦ Celebrações GAFI ✦</p>
                <h1>Aniversariantes de <span style="color:#38bdf8;">{nome_mes_atual}</span></h1>
                <div class="header-deco">🎉 🎂 🎈</div>
                <div class="header-count">
                    {'🎂 1 aniversariante' if total_mes == 1 else f'🎂 {total_mes} aniversariantes'}
                    {' — incluindo hoje! 🥳' if any(df_mes["data_nascimento"].dt.day == dia_atual) else ''}
                </div>
                <div class="print-data-evento-header">Data do Evento: 30/04/2026</div>
            </div>
        </div>

        <div class="mural-grid">
            {cartoes_html}
        </div>

        <div id="badge-orientacao" class="orientacao-badge"></div>
        <button id="btn-topo" class="btn-topo" onclick="voltarTopo()">↑ Topo</button>

        <div class="print-toolbar">
            <button class="btn-imprimir" onclick="imprimirCom('portrait')">🖨️ Imprimir A3 — Retrato</button>
            <button class="btn-imprimir btn-paisagem" onclick="imprimirCom('landscape')">🖨️ Imprimir A3 — Paisagem</button>
        </div>

        <script>
            var IS_TV = false;

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
            }});
        </script>
    </body>
    </html>
    """
    components.html(full_html, height=altura_iframe, scrolling=True)

# ── SUB‑MURAL RETROATIVO (meses 1,2,3) – Abril/2026 ────────────────────────
if not is_tv and mes_atual == 4 and hoje.year == 2026:
    df_retro = df[df["data_nascimento"].dt.month.isin([1, 2, 3])].copy()
    if not df_retro.empty:
        df_retro = df_retro.sort_values("data_nascimento")
        mini_cards = ""
        for _, row in df_retro.iterrows():
            nome_retro_raw = str(row.get("nome", "Sem nome")).strip()
            nome_retro = html_lib.escape(nome_retro_raw.title())
            dia_r = row["data_nascimento"].day if pd.notna(row["data_nascimento"]) else "?"
            mes_r = MESES_PTBR.get(row["data_nascimento"].month, "")
            img_url_r = str(row.get("foto_url", "")).strip().replace("'", "%27").replace('"', "%22")
            if img_url_r:
                foto_r = f'<img src="{img_url_r}" onerror="this.style.display=\'none\';this.nextElementSibling.style.display=\'flex\';" alt="Foto" /><div style="display:none;width:100%;height:100%;background:#e2e8f0;align-items:center;justify-content:center;font-size:2rem;">👤</div>'
            else:
                foto_r = '<div style="width:100%;height:100%;background:#e2e8f0;display:flex;align-items:center;justify-content:center;font-size:2rem;">👤</div>'

            mini_cards += f"""
            <div class="mini-polaroid">
                <div class="mini-foto">{foto_r}</div>
                <div class="mini-nome">{nome_retro}</div>
                <div class="mini-data">{dia_r} {mes_r}</div>
            </div>
            """

        sub_mural_html = f"""
        <!DOCTYPE html>
        <html>
        <head><meta charset="UTF-8">
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600&family=Playfair+Display:wght@700&display=swap" rel="stylesheet">
        <style>
            *, *::before, *::after {{ margin:0; padding:0; box-sizing:border-box; }}
            html {{
                {estilo_fundo}
                background-attachment: scroll !important;
                background-size: cover !important;
                background-position: center top !important;
                background-repeat: no-repeat !important;
                min-height: 100%;
            }}
            body {{
                background: transparent !important;
                display: flex;
                align-items: center;
                justify-content: center;
                min-height: 100vh;
                padding: 20px;
            }}
            .sub-mural-container {{
                background: rgba(255,255,255,0.85);
                backdrop-filter: blur(8px);
                border: 1px solid rgba(0,0,0,0.05);
                border-radius: 16px;
                padding: 24px 20px;
                margin: 0 auto;
                max-width: min(1400px, 96vw);
                text-align: center;
                box-shadow: 0 4px 16px rgba(0,0,0,0.08);
            }}
            .sub-mural-titulo {{
                font-family: 'Playfair Display', serif;
                font-size: 1.35rem;
                color: #1e293b;
                margin-bottom: 18px;
                font-weight: 700;
            }}
            .sub-mural-grid {{
                display: flex;
                flex-wrap: wrap;
                gap: 20px;
                justify-content: center;
            }}
            .mini-polaroid {{
                background: #fff;
                padding: 10px 10px 14px;
                border-radius: 4px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.06);
                width: 138px;
                text-align: center;
                transition: transform 0.25s ease;
            }}
            .mini-polaroid:hover {{
                transform: scale(1.05);
            }}
            .mini-foto {{
                width: 100%;
                aspect-ratio: 1;
                overflow: hidden;
                border-radius: 2px;
                margin-bottom: 6px;
            }}
            .mini-foto img {{
                width: 100%;
                height: 100%;
                object-fit: cover;
                display: block;
            }}
            .mini-nome {{
                font-family: 'Inter', sans-serif;
                font-size: 0.75rem;
                font-weight: 600;
                color: #1e293b;
                line-height: 1.2;
                word-break: break-word;
                overflow-wrap: break-word;
                white-space: normal;
                overflow: hidden;
                display: -webkit-box;
                -webkit-line-clamp: 2;
                -webkit-box-orient: vertical;
            }}
            .mini-data {{
                font-family: 'Inter', sans-serif;
                font-size: 0.65rem;
                color: #64748b;
                margin-top: 3px;
            }}
        </style></head>
        <body>
        <div class="sub-mural-container">
            <div class="sub-mural-titulo">📅 Aniversariantes dos meses anteriores</div>
            <div class="sub-mural-grid">{mini_cards}</div>
        </div>
        </body></html>
        """
        linhas = (len(df_retro) + 5) // 6
        altura_sub = linhas * 225 + 140
        components.html(sub_mural_html, height=altura_sub, scrolling=False)
