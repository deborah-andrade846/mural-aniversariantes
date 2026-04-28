import base64
import html as html_lib
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
from datetime import datetime
from utils import get_supabase, to_bool, cor_hex_valida, carregar_config

# ── CONSTANTE: tamanho máximo de imagem de fundo (2 MB) ──────────────────────
MAX_IMG_BYTES = 2 * 1024 * 1024

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
@st.cache_data(ttl=120)
def carregar_aniversariantes(_supabase):
    return _supabase.table("aniversariantes").select("*").execute().data or []

@st.cache_data(ttl=120)
def carregar_recados(_supabase):
    return _supabase.table("recados").select("*").execute().data or []

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
    
    # SEPARAÇÃO: Mês Atual vs Retroativos
    df_mes = df[df["data_nascimento"].dt.month == mes_atual].copy()

    df_retroativos = pd.DataFrame()
    if mes_atual == 4:
        df_retroativos = df[df["data_nascimento"].dt.month.isin([1, 2, 3])].copy()
        df_retroativos = df_retroativos.sort_values(
            by="data_nascimento",
            key=lambda s: s.dt.month * 100 + s.dt.day
        )

    if not df_mes.empty or not df_retroativos.empty:
        if not df_mes.empty:
            df_mes = df_mes.sort_values(
                by="data_nascimento",
                key=lambda s: s.dt.day.apply(lambda d: (0 if d == dia_atual else 1, d))
            )

        total_mes = len(df_mes)

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

        altura_iframe = 300
        
        df_todos_renderizados = pd.concat([df_mes, df_retroativos]) if not df_retroativos.empty else df_mes
        
        for _, row in df_todos_renderizados.iterrows():
            nome_r        = str(row.get("nome", ""))
            n_recados     = recados_por_pessoa.get(nome_r, 0)
            linhas_postit = max(1, (n_recados // 4) + 1)
            altura_iframe += 420 + linhas_postit * 170

        if not df_retroativos.empty:
            altura_iframe += 200

        # ── O SEU LAÇO ORIGINAL INTACTO (MÊS ATUAL) ───────────────────────────
        cards_html = ""
        for i, row in df_mes.iterrows():
            nome = html_lib.escape(str(row.get("nome", "Sem Nome")))
            curiosidade = html_lib.escape(str(row.get("curiosidade", "Gosta de surpresas!")))
            foto_url = str(row.get("foto_url", ""))
            
            eh_hoje = False
            str_dia = ""
            if pd.notnull(row.get("data_nascimento")):
                str_dia = f"{row['data_nascimento'].day:02d}/{row['data_nascimento'].month:02d}"
                eh_hoje = (row["data_nascimento"].day == dia_atual)

            classe_hoje = " hoje" if eh_hoje else ""
            badge_hoje  = '<div class="badge-hoje">✨ É HOJE! ✨</div>' if eh_hoje else ""

            if not foto_url:
                foto_url = f"https://api.dicebear.com/7.x/initials/svg?seed={nome}&backgroundColor=38bdf8,818cf8&textColor=ffffff"

            confete_html = ""
            if eh_hoje:
                pecas = ""
                for ci in range(12):
                    cor = CONFETE_CORES[ci % len(CONFETE_CORES)]
                    left = (ci * 7) % 100
                    delay = round((ci * 0.22) % 3, 2)
                    dur = round(2.5 + (ci % 3) * 0.5, 1)
                    pecas += (
                        f'<div class="confete-piece" '
                        f'style="left:{left}%;background:{cor};'
                        f'animation-duration:{dur}s;animation-delay:{delay}s;"></div>'
                    )
                confete_html = f'<div class="confete-wrapper">{pecas}</div>'

            n_recados_pessoa = 0
            post_its_html = ""

            if not liberar_recados:
                post_its_html = """
                <p class="sem-recados sem-recados-bloqueado">
                    🔒 Os recados serão revelados em breve!
                </p>"""
            elif not df_recados.empty and "para_quem" in df_recados.columns:
                nome_original = str(row.get("nome", "")).strip()
                recados_pessoa = df_recados[df_recados["para_quem"] == nome_original]
                n_recados_pessoa = len(recados_pessoa)
                
                if recados_pessoa.empty:
                    post_its_html = '<p class="sem-recados">📌 Seja o primeiro a deixar um recado!</p>'
                else:
                    for _, r_row in recados_pessoa.iterrows():
                        cor_idx = abs(hash(str(r_row.get("de_quem")) + str(r_row.get("mensagem")))) % len(POSTIT_COLORS)
                        cor_tema = POSTIT_COLORS[cor_idx]
                        
                        remetente = html_lib.escape(str(r_row.get("de_quem", "Anônimo")))
                        mensagem  = html_lib.escape(str(r_row.get("mensagem", "")))
                        
                        angulo = (hash(mensagem) % 6) - 3
                        
                        post_its_html += f"""
                        <div class="post-it" style="background:{cor_tema['bg']}; color:{cor_tema['text']}; box-shadow: 2px 4px 10px {cor_tema['shadow']}; transform: rotate({angulo}deg);">
                            <div class="post-it-msg">{mensagem}</div>
                            <div class="post-it-autor">- {remetente}</div>
                        </div>
                        """
            else:
                post_its_html = '<p class="sem-recados">📌 Seja o primeiro a deixar um recado!</p>'

            cards_html += f"""
            <div class="aniversariante-row{classe_hoje}">
                {confete_html}
                <div class="col-esquerda">
                    <div class="polaroid-container">
                        <div class="polaroid-wrapper">
                            <div class="polaroid">
                                <div class="foto-img" style="background-image: url('{foto_url}');"></div>
                                <div class="polaroid-caption">{nome}</div>
                            </div>
                        </div>
                    </div>
                    <div class="info-perfil">
                        <div class="nome">{nome}</div>
                        <div class="data-nasc">🎂 {str_dia} {badge_hoje}</div>
                        <div class="curiosidade">
                            <span class="curiosidade-label">Curiosidade:</span>
                            {curiosidade}
                        </div>
                    </div>
                </div>
                <div class="col-direita">
                    <div class="recados-titulo">💌 Recados ({n_recados_pessoa})</div>
                    <div class="recados-grid">
                        {post_its_html}
                    </div>
                </div>
            </div>
            """

        # ── O SEU LAÇO DUPLICADO PARA RETROATIVOS ─────────────────────────────
        cards_retro_html = ""
        if not df_retroativos.empty:
            for i, row in df_retroativos.iterrows():
                nome = html_lib.escape(str(row.get("nome", "Sem Nome")))
                curiosidade = html_lib.escape(str(row.get("curiosidade", "Gosta de surpresas!")))
                foto_url = str(row.get("foto_url", ""))
                
                eh_hoje = False
                str_dia = ""
                if pd.notnull(row.get("data_nascimento")):
                    str_dia = f"{row['data_nascimento'].day:02d}/{row['data_nascimento'].month:02d}"

                classe_hoje = ""
                badge_hoje  = ""

                if not foto_url:
                    foto_url = f"https://api.dicebear.com/7.x/initials/svg?seed={nome}&backgroundColor=38bdf8,818cf8&textColor=ffffff"

                confete_html = ""

                n_recados_pessoa = 0
                post_its_html = ""

                if not liberar_recados:
                    post_its_html = """
                    <p class="sem-recados sem-recados-bloqueado">
                        🔒 Os recados serão revelados em breve!
                    </p>"""
                elif not df_recados.empty and "para_quem" in df_recados.columns:
                    nome_original = str(row.get("nome", "")).strip()
                    recados_pessoa = df_recados[df_recados["para_quem"] == nome_original]
                    n_recados_pessoa = len(recados_pessoa)
                    
                    if recados_pessoa.empty:
                        post_its_html = '<p class="sem-recados">📌 Seja o primeiro a deixar um recado!</p>'
                    else:
                        for _, r_row in recados_pessoa.iterrows():
                            cor_idx = abs(hash(str(r_row.get("de_quem")) + str(r_row.get("mensagem")))) % len(POSTIT_COLORS)
                            cor_tema = POSTIT_COLORS[cor_idx]
                            
                            remetente = html_lib.escape(str(r_row.get("de_quem", "Anônimo")))
                            mensagem  = html_lib.escape(str(r_row.get("mensagem", "")))
                            
                            angulo = (hash(mensagem) % 6) - 3
                            
                            post_its_html += f"""
                            <div class="post-it" style="background:{cor_tema['bg']}; color:{cor_tema['text']}; box-shadow: 2px 4px 10px {cor_tema['shadow']}; transform: rotate({angulo}deg);">
                                <div class="post-it-msg">{mensagem}</div>
                                <div class="post-it-autor">- {remetente}</div>
                            </div>
                            """
                else:
                    post_its_html = '<p class="sem-recados">📌 Seja o primeiro a deixar um recado!</p>'

                cards_retro_html += f"""
                <div class="aniversariante-row{classe_hoje}">
                    {confete_html}
                    <div class="col-esquerda">
                        <div class="polaroid-container">
                            <div class="polaroid-wrapper">
                                <div class="polaroid">
                                    <div class="foto-img" style="background-image: url('{foto_url}');"></div>
                                    <div class="polaroid-caption">{nome}</div>
                                </div>
                            </div>
                        </div>
                        <div class="info-perfil">
                            <div class="nome">{nome}</div>
                            <div class="data-nasc">🎂 {str_dia} {badge_hoje}</div>
                            <div class="curiosidade">
                                <span class="curiosidade-label">Curiosidade:</span>
                                {curiosidade}
                            </div>
                        </div>
                    </div>
                    <div class="col-direita">
                        <div class="recados-titulo">💌 Recados ({n_recados_pessoa})</div>
                        <div class="recados-grid">
                            {post_its_html}
                        </div>
                    </div>
                </div>
                """

        # ── HTML BASE E MONTAGEM FINAL DA TELA ────────────────────────────────
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
                .header-count {{
                    display:inline-block; margin-top:15px; padding:6px 18px;
                    background:rgba(0,0,0,0.25); border-radius:20px;
                    font-size:0.85rem; font-weight:600; letter-spacing:0.5px;
                    border:1px solid rgba(255,255,255,0.1); text-transform:uppercase;
                }}

                /* --- DATA DE IMPRESSÃO --- */
                .data-evento-print {{ display: none; }}

                /* ══ CONTAINER DOS CARDS ═════════════════════════════════════ */
                .cards-container {{
                    display:flex; flex-direction:column; gap:48px;
                    width:100%; max-width:min(1200px, 94vw);
                }}

                /* ══ CARD ANIVERSARIANTE ═════════════════════════════════════ */
                .aniversariante-row {{
                    background: rgba(255,255,255,0.08);
                    backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px);
                    border: 1px solid rgba(255,255,255,0.2);
                    border-radius: 24px; padding: clamp(24px, 4vw, 40px);
                    display: grid; grid-template-columns: minmax(300px, 1fr) 2fr; gap: clamp(24px, 4vw, 40px);
                    position: relative; overflow: hidden;
                    box-shadow: 0 8px 32px rgba(0,0,0,0.15);
                    transition: transform 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275), box-shadow 0.3s ease;
                    animation: fadeInUp 0.7s ease both;
                }}
                .aniversariante-row::before {{
                    content:''; position:absolute; top:0; left:0; right:0; height:4px;
                    background: linear-gradient(90deg,#38bdf8,#818cf8,#f472b6);
                    border-radius: 20px 20px 0 0;
                }}
                .aniversariante-row:hover {{
                    transform: translateY(-3px); box-shadow: 0 20px 50px rgba(0,0,0,0.25);
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
                    background: linear-gradient(135deg,#f59e0b,#fbbf24); color: #78350f;
                    font-family:'Inter',sans-serif; font-size:0.72rem; font-weight:800;
                    letter-spacing:1.5px; text-transform:uppercase; padding:5px 14px;
                    border-radius:20px; margin-top:8px;
                    box-shadow:0 3px 10px rgba(245,158,11,0.4);
                    animation: brilho 1.8s ease-in-out infinite;
                }}

                /* ══ CONFETE ═════════════════════════════════════════════════ */
                .confete-wrapper {{
                    position:absolute; top:0; left:0; width:100%; height:100%;
                    pointer-events:none; overflow:hidden; border-radius:22px; z-index:0;
                }}
                .confete-piece {{
                    position:absolute; top:-20px; width:8px; height:8px; border-radius:2px;
                    animation: confete 3s ease-in infinite;
                }}

                /* ══ POLAROID ════════════════════════════════════════════════ */
                .polaroid-container {{
                    width:100%; display:flex; align-items:center; justify-content:center;
                    padding:10px; position:relative; z-index:1;
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
                    position:relative; transform:rotate(-2deg);
                    transition:transform 0.4s ease, box-shadow 0.4s ease; width:100%;
                }}
                .polaroid:hover {{
                    transform:rotate(0deg) scale(1.02); z-index:2;
                    box-shadow:0 24px 50px rgba(0,0,0,0.25);
                }}
                .foto-img {{
                    width:100%; aspect-ratio:1/1; background-color:#e2e8f0;
                    background-size:cover; background-position:center;
                    border:1px solid rgba(0,0,0,0.05); border-radius:2px;
                }}
                .polaroid-caption {{
                    position:absolute; bottom:18px; left:0; right:0; text-align:center;
                    font-family:'Caveat',cursive; font-size:1.8rem; font-weight:700;
                    color:#1e293b; letter-spacing:1px; line-height:1;
                }}

                /* ══ INFORMAÇÕES DE PERFIL ═══════════════════════════════════ */
                .info-perfil {{ position:relative; z-index:1; margin-top:24px; text-align:center; }}
                .info-perfil .nome {{
                    font-family:'Playfair Display',serif; font-size:2.2rem;
                    font-weight:900; margin-bottom:8px; line-height:1.2;
                    text-shadow:0 2px 10px rgba(0,0,0,0.4);
                }}
                .info-perfil .data-nasc {{
                    font-size:1.15rem; font-weight:600; color:#cbd5e1;
                    margin-bottom:20px; display:flex; flex-direction:column;
                    align-items:center; text-shadow:0 1px 3px rgba(0,0,0,0.6);
                }}
                .aniversariante-row.hoje .info-perfil .nome,
                .aniversariante-row.hoje .info-perfil .data-nasc {{ color:#451a03; text-shadow:none; }}

                .curiosidade {{
                    background:rgba(0,0,0,0.25); border-radius:12px;
                    padding:16px; font-size:0.95rem; line-height:1.5; color:#f1f5f9;
                    border-left:4px solid #38bdf8; text-align:left; box-shadow:inset 0 2px 4px rgba(0,0,0,0.1);
                }}
                .aniversariante-row.hoje .curiosidade {{
                    background:rgba(255,255,255,0.5); color:#78350f; border-left-color:#f59e0b;
                }}
                .curiosidade-label {{
                    display:block; font-weight:700; font-size:0.8rem;
                    text-transform:uppercase; letter-spacing:1px; margin-bottom:6px;
                    color:#94a3b8;
                }}
                .aniversariante-row.hoje .curiosidade-label {{ color:#92400e; }}

                /* ══ RECADOS (POST-ITS) ══════════════════════════════════════ */
                .col-direita {{ position:relative; z-index:1; display:flex; flex-direction:column; }}
                .recados-titulo {{
                    font-family:'Playfair Display',serif; font-size:1.6rem;
                    font-weight:700; margin-bottom:24px; border-bottom:2px solid rgba(255,255,255,0.2);
                    padding-bottom:10px; color:#ffffff; text-shadow:0 2px 8px rgba(0,0,0,0.5);
                }}
                .aniversariante-row.hoje .recados-titulo {{
                    color:#451a03; border-bottom-color:rgba(120,53,15,0.2); text-shadow:none;
                }}
                .recados-grid {{
                    display:grid; grid-template-columns:repeat(auto-fill, minmax(140px, 1fr));
                    gap:18px; align-content:flex-start;
                }}
                .post-it {{
                    padding:18px 15px 14px; width:clamp(140px,18vw,175px); min-height:130px;
                    font-family:'Caveat',cursive; font-size:1.05rem;
                    border-radius:3px 16px 3px 3px; display:flex; flex-direction:column;
                    justify-content:flex-start; gap:10px; position:relative;
                    transition:transform 0.28s ease, box-shadow 0.28s ease;
                }}
                .post-it::before {{
                    content:'📌'; position:absolute; top:-12px; left:50%;
                    transform:translateX(-50%); font-size:1.2rem; filter:drop-shadow(0 2px 3px rgba(0,0,0,0.2));
                }}
                .post-it:hover {{ transform:scale(1.08) translateY(-4px) rotate(1deg) !important; z-index:10; }}
                .post-it-msg {{
                    line-height:1.35; font-weight:700; color:rgba(0,0,0,0.85); padding-top:4px;
                    flex:1; overflow:hidden; display:-webkit-box; -webkit-line-clamp:5;
                    -webkit-box-orient:vertical; word-break:break-word;
                }}
                .post-it-autor {{
                    font-size:0.88rem; font-weight:700; color:rgba(0,0,0,0.6); text-align:right;
                    margin-top:auto; border-top:1px dashed rgba(0,0,0,0.15); padding-top:8px;
                    overflow:hidden; white-space:nowrap; text-overflow:ellipsis;
                }}
                .sem-recados {{
                    color:#475569; text-shadow:0 1px 3px rgba(255,255,255,0.6);
                    font-size:1.05rem; font-style:italic; padding:28px 0;
                    display:flex; align-items:center; gap:8px;
                }}
                .sem-recados-bloqueado {{
                    background:rgba(100,116,139,0.08); border:1px dashed rgba(100,116,139,0.3);
                    border-radius:10px; padding:18px 22px; color:#64748b; font-style:normal;
                    font-weight:600; letter-spacing:0.3px;
                }}

                /* ══ BOTÃO VOLTAR AO TOPO ════════════════════════════════════ */
                .btn-topo {{
                    position:fixed; bottom:30px; right:30px; background:rgba(15,23,42,0.8);
                    color:white; border:none; border-radius:50%; width:50px; height:50px;
                    font-size:1.5rem; cursor:pointer; z-index:999;
                    box-shadow:0 4px 12px rgba(0,0,0,0.3); transition:all 0.3s ease;
                    opacity:0; visibility:hidden; transform:translateY(20px);
                }}
                .btn-topo.visivel {{ opacity:1; visibility:visible; transform:translateY(0); }}
                .btn-topo:hover {{ background:#0f172a; transform:translateY(-5px) scale(1.1); }}

                /* ══ IMPRESSÃO & TOOLBAR ═════════════════════════════════════ */
                .print-toolbar {{
                    position: fixed; bottom: 20px; left: 20px; z-index: 1000;
                    display: flex; gap: 10px;
                    background: rgba(0,0,0,0.6); padding: 10px 15px;
                    border-radius: 12px; backdrop-filter: blur(8px);
                }}
                .btn-imprimir {{
                    background: #3b82f6; color: white; border: none;
                    padding: 8px 16px; border-radius: 6px; font-weight: 600;
                    cursor: pointer; transition: background 0.2s;
                }}
                .btn-imprimir:hover {{ background: #2563eb; }}
                .btn-paisagem {{ background: #8b5cf6; }}
                .btn-paisagem:hover {{ background: #7c3aed; }}
                .orientacao-badge {{
                    position: fixed; top: 15px; left: 15px; background: rgba(0,0,0,0.7);
                    color: white; padding: 6px 12px; border-radius: 20px;
                    font-size: 0.8rem; font-weight: bold; z-index: 1000;
                    display: none; letter-spacing: 1px;
                }}

                /* ── Media Query Impressão ── */
                @media print {{
                    @page {{ margin: 10mm; size: A3; }}
                    html, body {{ background: none !important; margin:0; padding:0; height:auto; }}
                    .print-toolbar, .btn-topo, .header-deco {{ display: none !important; }}
                    .mural-header {{ margin-bottom:20px; animation:none; }}
                    .mural-header-inner {{
                        background: none !important; box-shadow: none !important; border: none !important;
                        -webkit-backdrop-filter: none; padding: 0; width: 100%;
                    }}
                    .mural-header-inner::before {{ display:none; }}
                    h1 {{ color:#0f172a !important; text-shadow:none !important; }}
                    .subtitulo, .header-count {{ color:#475569 !important; text-shadow:none !important; background:none !important; border:none !important; }}
                    .mes-destaque {{ background:none; -webkit-text-fill-color:#0f172a; color:#0f172a; }}
                    
                    /* Trazendo a data do evento apenas para impressão */
                    .data-evento-print {{
                        display: block !important;
                        font-family: 'Playfair Display', serif;
                        font-size: 1.3rem;
                        font-weight: 700;
                        color: #0f172a;
                        margin-top: 10px;
                    }}

                    .cards-container {{ gap:20px; }}
                    .aniversariante-row {{
                        background: white !important; border: 1px solid #cbd5e1 !important;
                        box-shadow: none !important; break-inside: avoid; animation:none; padding: 20px;
                    }}
                    .aniversariante-row::before {{ display:none; }}
                    .polaroid-wrapper::before {{ display:none; }}
                    .polaroid {{ transform:none !important; box-shadow:none !important; border:1px solid #e2e8f0; }}
                    .polaroid-caption {{ color:#000 !important; }}
                    .info-perfil .nome {{ color:#000 !important; text-shadow:none !important; }}
                    .info-perfil .data-nasc {{ color:#333 !important; text-shadow:none !important; }}
                    .curiosidade {{ background:#f8fafc !important; color:#000 !important; box-shadow:none !important; border-left-color:#94a3b8 !important; }}
                    .curiosidade-label {{ color:#64748b !important; }}
                    .recados-titulo {{ color:#000 !important; border-bottom-color:#cbd5e1 !important; text-shadow:none !important; }}
                    .post-it {{ break-inside: avoid; transform:none !important; box-shadow:none !important; border:1px solid #cbd5e1 !important; background:#fff !important; }}
                    .confete-wrapper {{ display:none !important; }}
                }}

                /* ── Responsividade ── */
                @media(max-width:850px) {{
                    .aniversariante-row {{ grid-template-columns:1fr; gap:30px; }}
                    .col-esquerda {{ display:flex; flex-direction:column; align-items:center; }}
                    .info-perfil {{ width:100%; }}
                    .recados-grid {{ justify-content:center; }}
                }}

                /* ── Animações ── */
                @keyframes fadeInUp {{ from {{ opacity:0; transform:translateY(40px); }} to {{ opacity:1; transform:translateY(0); }} }}
                @keyframes fadeInDown {{ from {{ opacity:0; transform:translateY(-30px); }} to {{ opacity:1; transform:translateY(0); }} }}
                @keyframes brilho {{ 0% {{ box-shadow:0 0 10px rgba(245,158,11,0.4); }} 50% {{ box-shadow:0 0 25px rgba(245,158,11,0.8); }} 100% {{ box-shadow:0 0 10px rgba(245,158,11,0.4); }} }}
                @keyframes pulsoHoje {{ 0% {{ transform:scale(1); box-shadow:0 8px 32px rgba(0,0,0,0.15); }} 50% {{ transform:scale(1.015); box-shadow:0 15px 45px rgba(245,158,11,0.3); }} 100% {{ transform:scale(1); box-shadow:0 8px 32px rgba(0,0,0,0.15); }} }}
                @keyframes confete {{ 0% {{ transform:translateY(0) rotate(0deg) scale(1); opacity:1; }} 100% {{ transform:translateY(350px) rotate(720deg) scale(0.5); opacity:0; }} }}
            </style>
        </head>
        <body>
            <script>
                var IS_TV = {str(is_tv).lower()};
                
                function applyOrientation(ori) {{
                    var oldStyle = document.getElementById('print-orientation-style');
                    if (oldStyle) oldStyle.remove();
                    var style = document.createElement('style');
                    style.id = 'print-orientation-style';
                    style.innerHTML = '@media print {{ @page {{ size: A3 ' + ori + '; }} }}';
                    document.head.appendChild(style);
                    var badge = document.getElementById('badge-orientacao');
                    badge.innerText = ori === 'landscape' ? '↔ PAISAGEM A3' : '↕ RETRATO A3';
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
                function voltarTopo() {{ window.scrollTo({{ top: 0, behavior: 'smooth' }}); }}

                document.addEventListener('DOMContentLoaded', function() {{
                    applyOrientation('portrait');
                    if (IS_TV) {{
                        var toolbar = document.querySelector('.print-toolbar');
                        var badge = document.getElementById('badge-orientacao');
                        var topo = document.getElementById('btn-topo');
                        if (toolbar) toolbar.style.display = 'none';
                        if (badge) badge.style.display = 'none';
                        if (topo) topo.style.display = 'none';

                        setTimeout(function() {{
                            try {{ window.parent.location.reload(); }}
                            catch(e) {{ window.location.reload(); }}
                        }}, 300000);
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
                    
                    <div class="data-evento-print">Data do Evento: 30/04</div>
                    
                    <div class="header-deco">🎉 🎂 🎈 🎊 🎁</div>
                    <div class="header-count">
                        {'🎂 1 aniversariante' if total_mes == 1 else f'🎂 {total_mes} aniversariantes'}
                        {' — incluindo hoje! 🥳' if any(df_mes["data_nascimento"].dt.day == dia_atual) else ''}
                    </div>
                </div>
            </div>
            
            <div class="cards-container">
                {cards_html}
            </div>
            
            {f'''
            <div class="mural-header" style="margin-top: 80px; margin-bottom: 40px;">
                <div class="mural-header-inner" style="padding: 15px 30px;">
                    <p class="subtitulo">✦ Retroativos ✦</p>
                    <h1 style="font-size: clamp(1.6rem, 3vw, 2.5rem);">Meses Anteriores</h1>
                </div>
            </div>
            <div class="cards-container">
                {cards_retro_html}
            </div>
            ''' if cards_retro_html else ''}
            
        </body>
        </html>
        """

        components.html(html_base, height=altura_iframe, scrolling=False)

    else:
        # ── ESTADO VAZIO (Nenhum aniversariante no mês ou retroativo) ─────────
        html_vazio = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <link rel="preconnect" href="https://fonts.googleapis.com">
            <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,700;0,900;1,700&family=Inter:wght@400;600&display=swap" rel="stylesheet">
            <style>
                *, *::before, *::after {{ box-sizing: border-box; }}
                html, body {{ margin:0; padding:0; width:100%; height:100%; }}
                html {{
                    {estilo_fundo}
                    background-attachment: fixed !important;
                    background-size: cover !important;
                    background-position: center top !important;
                }}
                body {{
                    background: transparent !important;
                    display: flex; justify-content: center; align-items: center;
                    font-family: 'Inter', sans-serif;
                }}
                @keyframes fadeInUp {{
                    from{{ opacity:0; transform:translateY(30px); }}
                    to{{ opacity:1; transform:translateY(0); }}
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
                    Vamos esperar as próximas! 🎉
                </div>
            </div>
        </body>
        </html>
        """
        components.html(html_vazio, height=500, scrolling=False)
