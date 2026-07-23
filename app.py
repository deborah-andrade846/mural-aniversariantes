import base64
import hashlib
import html as html_lib
import uuid
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

def _parse_mes_admin(val):
    """Mês salvo na config: int 1-12, ou 0 para 'automático' (mês atual)."""
    try:
        m = int(val)
        return m if 1 <= m <= 12 else 0
    except (TypeError, ValueError):
        return 0

# ── CONEXÃO & CONFIG ──────────────────────────────────────────────────────────
supabase = get_supabase()
config   = carregar_config()

exibir_mural     = to_bool(config.get("exibir_mural",    False))
liberar_recados  = to_bool(config.get("liberar_recados", False))
liberar_cadastro = to_bool(config.get("liberar_cadastro", True))

# ── MODO TV ───────────────────────────────────────────────────────────────────
# Precedência: a URL manda. ?tv=false força o modo normal (saída de
# emergência para reaver o painel admin); ?tv=true força o modo TV;
# sem parâmetro, vale o que estiver salvo no painel (config modo_tv).
_tv_param = st.query_params.get("tv")
if _tv_param == "false":
    is_tv = False
elif _tv_param == "true":
    is_tv = True
else:
    is_tv = to_bool(config.get("modo_tv", False))

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

# Na TV, esconde a barra lateral para o público (telão limpo), mas mantém
# para o admin — assim ele nunca fica preso e pode desligar o modo TV.
if is_tv and not modo_admin:
    st.markdown(
        "<style>[data-testid='stSidebar']{display:none;}</style>",
        unsafe_allow_html=True,
    )

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
        novo_pesquisa = st.checkbox("Libertar Aba de Pesquisa", value=to_bool(config.get("liberar_pesquisa", True)))

    with st.sidebar.expander("📺 Modo TV (telão)", expanded=False):
        st.caption(
            "Liga o carrossel no telão e fixa o mês exibido, sem precisar "
            "mexer na URL. A TV atualiza sozinha em até 5 min."
        )
        novo_modo_tv = st.checkbox(
            "📺 Ativar modo TV (carrossel)",
            value=to_bool(config.get("modo_tv", False)),
        )
        _opcoes_mes_tv = [0] + list(MESES_PTBR.keys())   # 0 = automático
        _mes_tv_salvo  = _parse_mes_admin(config.get("mes_tv"))
        novo_mes_tv = st.selectbox(
            "Mês exibido na TV",
            options=_opcoes_mes_tv,
            index=_opcoes_mes_tv.index(_mes_tv_salvo),
            format_func=lambda m: "Automático (mês atual)" if m == 0 else MESES_PTBR[m],
        )
        if novo_modo_tv:
            st.info("⚠️ Com o modo TV ligado, todos que abrirem o mural verão o carrossel (sem o menu lateral).")

    with st.sidebar.expander("🎨 Personalização Visual", expanded=False):
        cor_fundo_banco = config.get("cor_fundo")
        if cor_hex_valida(cor_fundo_banco):
            cor_fundo = st.color_picker("Cor base do Mural", value=cor_fundo_banco)
        else:
            cor_fundo = st.color_picker("Cor base do Mural")

        imagem_fundo = st.file_uploader("Imagem de Fundo", type=["jpg", "png", "jpeg"])

    with st.sidebar.expander("📅 Dados do Evento", expanded=False):
        st.caption(
            "Aparecem no cabeçalho ao **imprimir** o mural (o cartaz do evento)."
        )
        novo_data_evento = st.text_input(
            "Data do evento",
            value=str(config.get("data_evento", "") or ""),
            placeholder="Ex.: 30/07/2026",
        )
        novo_local_evento = st.text_input(
            "Local do evento",
            value=str(config.get("local_evento", "") or ""),
            placeholder="Ex.: Refeitório da GAFI",
        )

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
                "background-size: contain; background-position: center top; background-repeat: no-repeat;"
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

    with st.sidebar.expander("🔓 Resetar senha de perfil", expanded=False):
        st.caption(
            "Para quem esqueceu a senha. O reset libera o perfil para a pessoa "
            "criar uma senha nova na aba **Cadastro** — os dados (foto, "
            "curiosidade, data) são mantidos."
        )
        try:
            pessoas = carregar_aniversariantes(supabase)
            # Apenas perfis bloqueados (já completados, exigem senha para editar)
            bloqueados = [
                p for p in pessoas
                if to_bool(p.get("perfil_completo", False)) and p.get("id") is not None
            ]
            if not bloqueados:
                st.info("Nenhum perfil com senha definida no momento.")
            else:
                bloqueados = sorted(bloqueados, key=lambda p: str(p.get("nome", "")).lower())
                opcoes = {
                    f'{p.get("nome", "Sem nome")} (#{p["id"]})': p["id"]
                    for p in bloqueados
                }
                escolha = st.selectbox(
                    "Selecione o perfil",
                    options=list(opcoes.keys()),
                    key="reset_senha_sel",
                )
                if st.button("🔓 Resetar senha", use_container_width=True, key="reset_senha_btn"):
                    pid = opcoes[escolha]
                    try:
                        supabase.table("aniversariantes").update(
                            {"perfil_completo": False, "senha_perfil": None}
                        ).eq("id", pid).execute()
                        carregar_aniversariantes.clear()
                        st.success(
                            f"✅ Senha resetada! Avise **{escolha.rsplit(' (#', 1)[0]}** "
                            "para definir uma nova senha na aba Cadastro."
                        )
                    except Exception as e:
                        st.error(f"Erro ao resetar: {e}")
        except Exception:
            st.warning("Não foi possível carregar a lista de perfis.")

    with st.sidebar.expander("🔗 Fotos para Link", expanded=False):
        st.caption(
            "Transforme fotos em links públicos para colar na planilha "
            "(coluna `foto_url`). Pode enviar várias de uma vez."
        )
        fotos_link = st.file_uploader(
            "Fotos",
            type=["jpg", "jpeg", "png"],
            accept_multiple_files=True,
            key="admin_fotos_link",
        )
        if fotos_link and st.button(
            "🚀 Gerar links", key="admin_gerar_links", use_container_width=True
        ):
            resultados_links = []
            barra_links = st.progress(0.0)
            for i, arq in enumerate(fotos_link):
                nome_base = arq.name.rsplit(".", 1)[0]
                try:
                    ext      = arq.name.split(".")[-1].lower()
                    nome_arq = f"{uuid.uuid4()}.{ext}"
                    conteudo = arq.getvalue()
                    try:
                        supabase.storage.from_("fotos_mural").upload(
                            nome_arq, conteudo,
                            {"content-type": arq.type or "image/jpeg"},
                        )
                    except Exception:
                        supabase.storage.from_("fotos_mural").upload(nome_arq, conteudo)
                    url = supabase.storage.from_("fotos_mural").get_public_url(nome_arq)
                    resultados_links.append({"nome": nome_base, "link": url})
                except Exception as e:
                    resultados_links.append({"nome": nome_base, "link": f"ERRO: {e}"})
                barra_links.progress((i + 1) / len(fotos_link))
            st.session_state["admin_resultados_links"] = resultados_links

        resultados_links = st.session_state.get("admin_resultados_links")
        if resultados_links:
            df_links = pd.DataFrame(resultados_links)
            st.dataframe(df_links, use_container_width=True, hide_index=True)
            st.download_button(
                "⬇️ Baixar CSV (nome, link)",
                data=df_links.to_csv(index=False).encode("utf-8"),
                file_name="fotos_links.csv",
                mime="text/csv",
                use_container_width=True,
                key="admin_csv_links",
            )
            st.caption("Copie cada link (ícone de copiar no canto do campo):")
            for r in resultados_links:
                if not str(r["link"]).startswith("ERRO"):
                    st.code(r["link"], language=None)

    with st.sidebar.expander("🎬 Vídeo do Mural", expanded=False):
        st.caption(
            "Gera um vídeo com um aniversariante por vez (estilo TV) para os "
            "comunicados. Abre o estúdio na área principal, à direita."
        )
        st.selectbox(
            "Mês do vídeo",
            options=list(MESES_PTBR.keys()),
            index=datetime.now().month - 1,
            format_func=lambda m: MESES_PTBR[m],
            key="video_mes",
        )
        st.slider("Segundos por card", min_value=2, max_value=8, value=4, key="video_segs")
        st.checkbox("▶️ Abrir estúdio de vídeo", key="video_abrir")
        if st.session_state.get("video_abrir"):
            st.info("O estúdio abriu na área principal. Desmarque para voltar ao mural.")

    st.sidebar.write("")
    col_save, col_cache = st.sidebar.columns(2)

    if col_save.button("💾 Guardar", type="primary", use_container_width=True):
        atualizar_config("liberar_cadastro", novo_cadastro)
        atualizar_config("liberar_recados",  novo_recados)
        atualizar_config("exibir_mural",     novo_exibir)
        atualizar_config("cor_fundo",        cor_fundo)
        atualizar_config("liberar_pesquisa", novo_pesquisa)
        atualizar_config("modo_tv", novo_modo_tv)
        atualizar_config("mes_tv", novo_mes_tv if novo_mes_tv != 0 else "")
        atualizar_config("data_evento",  novo_data_evento.strip())
        atualizar_config("local_evento", novo_local_evento.strip())
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

# ── ESTÚDIO DE VÍDEO (função do admin) ────────────────────────────────────────
# Quando o admin liga "Abrir estúdio de vídeo" no painel, o estúdio ocupa a
# área principal e o mural não é renderizado (evita conflito de layout).
if modo_admin and st.session_state.get("video_abrir"):
    from video_studio import render_estudio
    render_estudio(
        supabase,
        st.session_state.get("video_mes", datetime.now().month),
        st.session_state.get("video_segs", 4),
        MESES_PTBR,
        data_evento=str(config.get("data_evento", "") or "").strip(),
        local_evento=str(config.get("local_evento", "") or "").strip(),
    )
    st.stop()

# ── ESTILO DE FUNDO (não-admin) ───────────────────────────────────────────────
if not modo_admin:
    imagem_salva = config.get("imagem_fundo", "")
    cor_salva    = config.get("cor_fundo")
    if imagem_salva:
        estilo_fundo = (
            f"background-image: url('{imagem_salva}'); "
            "background-size: contain; background-position: center top; background-repeat: no-repeat;"
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
            background-attachment: fixed !important;
            background-size: cover !important;
            background-position: center center !important;
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
hoje      = datetime.now()
dia_atual = hoje.day

# ── SELETOR DE MÊS ───────────────────────────────────────────────────────────
# Precedência: URL (?mes=6) > config do painel (mes_tv) > mês atual.
# Útil na TV: comemorações que acontecem fora do mês de aniversário.
def _parse_mes(val, default):
    try:
        m = int(val)
        return m if 1 <= m <= 12 else default
    except (TypeError, ValueError):
        return default

mes_config_default = _parse_mes(config.get("mes_tv"), hoje.month)
mes_url_default    = _parse_mes(st.query_params.get("mes"), mes_config_default)

if not is_tv:
    col_mes, _ = st.columns([1, 3])
    with col_mes:
        mes_selecionado = st.selectbox(
            "📅 Mês do Mural",
            options=list(MESES_PTBR.keys()),
            index=mes_url_default - 1,
            format_func=lambda m: MESES_PTBR[m],
            key="mes_mural",
        )
else:
    mes_selecionado = mes_url_default

mes_atual      = mes_selecionado
nome_mes_atual = MESES_PTBR[mes_atual]

dia_atual_efetivo = dia_atual if mes_atual == hoje.month else -1

# ── ATALHO PARA DEIXAR UM RECADO ──────────────────────────────────────────────
# Botão nativo do Streamlit (fora do iframe) que leva à aba de Recados,
# onde a pessoa escreve e envia a mensagem. Aparece quando os recados
# estão liberados.
if liberar_recados:
    st.markdown("""
        <style>
            /* botão de recado: bem visível e com cara de botão */
            div[data-testid="stLinkButton"] > a {
                padding: 0.6rem 1.2rem !important;
                border-radius: 14px !important;
                background: linear-gradient(135deg,#0ea5e9,#f472b6) !important;
                color: #ffffff !important;
                border: none !important;
                box-shadow: 0 8px 22px rgba(14,165,233,0.5) !important;
            }
            /* O texto do botão fica num elemento interno (p/div/span) com
               tamanho próprio, então a fonte precisa ser aplicada nele. */
            div[data-testid="stLinkButton"] > a,
            div[data-testid="stLinkButton"] > a p,
            div[data-testid="stLinkButton"] > a div,
            div[data-testid="stLinkButton"] > a span {
                font-size: 1.5rem !important;
                font-weight: 500 !important;
                letter-spacing: 0.3px !important;
                line-height: 1.2 !important;
            }
            div[data-testid="stLinkButton"] > a:hover {
                filter: brightness(1.05);
                transform: translateY(-2px);
            }
        </style>
    """, unsafe_allow_html=True)
    # Posiciona o botão no canto superior direito, com boa área de toque.
    _rc_esq, _rc_btn = st.columns([3, 1])
    with _rc_btn:
        st.link_button(
            "✍️ Deixar um recado",
            "/Recados",
            type="primary",
            use_container_width=True,
        )

if dados:
    df = pd.DataFrame(dados)
    df["data_nascimento"] = pd.to_datetime(df["data_nascimento"], errors="coerce")
    df_mes = df[df["data_nascimento"].dt.month == mes_atual].copy()

    if not df_mes.empty:
        df_mes = df_mes.sort_values(
            by="data_nascimento",
            key=lambda s: s.dt.day.apply(lambda d: (0 if d == dia_atual_efetivo else 1, d))
        )

        total_mes = len(df_mes)

        # ── Dados do evento (editáveis no painel admin) ───────────────────────
        data_evento  = str(config.get("data_evento", "") or "").strip()
        local_evento = str(config.get("local_evento", "") or "").strip()
        _partes_evento = []
        if data_evento:
            _partes_evento.append("📅 Data do Evento: " + html_lib.escape(data_evento))
        if local_evento:
            _partes_evento.append("📍 Local: " + html_lib.escape(local_evento))
        evento_html = (
            f'<div class="evento-info">{" &nbsp;•&nbsp; ".join(_partes_evento)}</div>'
            if _partes_evento else ""
        )

        # ── Fundo para impressão: <img> real (imprime mesmo sem "gráficos de
        #    segundo plano" marcado, ao contrário de background CSS) ───────────
        fundo_img_url = str(config.get("imagem_fundo", "") or "").strip()
        fundo_print_img = (
            f'<img class="print-bg-img" src="{fundo_img_url}" alt="" aria-hidden="true">'
            if fundo_img_url else ""
        )

        st.markdown(f"""
        <style>
            .block-container {{
                padding-left: 1rem !important;
                padding-right: 1rem !important;
                padding-top: 1rem !important;
                max-width: 100% !important;
            }}
            /* Fundo fixo no documento principal (fora do iframe) para que a
               imagem permaneça parada enquanto o mural rola. */
            .stApp {{
                {estilo_fundo}
                background-attachment: fixed !important;
                background-size: cover !important;
                background-position: center center !important;
                background-repeat: no-repeat !important;
            }}
            iframe[title="streamlit_components_v1.html"] {{
                width: 100% !important;
                border: none !important;
                background: transparent !important;
            }}
        </style>
        """, unsafe_allow_html=True)

        recados_por_pessoa = {}
        if not df_recados.empty and "para_quem" in df_recados.columns:
            recados_por_pessoa = df_recados["para_quem"].value_counts().to_dict()

        altura_iframe = 280
        for _, row in df_mes.iterrows():
            nome_r        = str(row.get("nome", ""))
            n_recados     = recados_por_pessoa.get(nome_r, 0)
            linhas_postit = max(1, (n_recados // 4) + 1)
            altura_iframe += 360 + linhas_postit * 150

        html_base = f"""
        <!DOCTYPE html>
        <html class="{'tv' if is_tv else ''}">
        <head>
            <meta charset="UTF-8">
            <link rel="preconnect" href="https://fonts.googleapis.com">
            <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,700;0,900;1,700&family=Inter:wght@300;400;500;600;700&family=Caveat:wght@500;700&display=swap" rel="stylesheet">
            <style>
                *, *::before, *::after {{ margin:0; padding:0; box-sizing:border-box; }}

                html {{
                    /* Fundo transparente: a imagem fica no .stApp (documento pai),
                       fixa em relação à janela. Apenas a impressão repõe o fundo. */
                    background: transparent !important;
                    min-height: 100%;
                }}
                body {{
                    background: transparent !important;
                    font-family: 'Inter', sans-serif;
                    color: #f8fafc;
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    padding: 20px 16px 32px;
                    min-height: 100vh;
                    width: 100%;
                }}
                /* Sem overlay de escurecimento: o fundo festivo aparece
                   uniforme em toda a tela. O contraste do texto é garantido
                   pelos próprios fundos do cabeçalho e dos cards. */
                .mural-header, .mural-grid {{ position: relative; z-index: 1; }}

                /* ══ HEADER ══════════════════════════════════════════════════ */
                .mural-header {{
                    text-align: center; margin-bottom: 28px;
                    width: 100%;
                    max-width: min(1400px, 96vw);
                    animation: fadeInDown 0.9s ease both;
                }}
                .mural-header-inner {{
                    /* Sem fundo: o cabeçalho fica direto sobre a imagem; a
                       legibilidade vem da sombra do texto. */
                    background: transparent;
                    border: none; box-shadow: none;
                    padding: clamp(20px,3.5vw,34px) clamp(34px,7vw,90px) clamp(18px,2.6vw,28px);
                    width: fit-content;
                    max-width: 95vw;
                    display: inline-block; position: relative; overflow: visible;
                    margin: 0 auto;
                }}
                .mural-header .subtitulo {{
                    font-family:'Inter',sans-serif; font-weight:700; font-size:0.8rem;
                    letter-spacing:7px; text-transform:uppercase; color:#fcd34d;
                    text-shadow:0 1px 2px rgba(0,0,0,0.85),
                                0 0 8px rgba(0,0,0,0.5);
                    margin-bottom:8px;
                }}
                .mural-header h1 {{
                    font-family:'Playfair Display',serif;
                    font-size:clamp(2.1rem,4vw,3.8rem);
                    font-weight:900; color:#fffdf7;
                    /* Halo escuro nítido (sem grandes desfoques que borram). */
                    text-shadow:0 1px 1px rgba(0,0,0,0.55),
                                0 2px 4px rgba(0,0,0,0.65),
                                0 0 6px rgba(0,0,0,0.35);
                    line-height:1.15; letter-spacing:-0.5px;
                    white-space: nowrap;
                }}
                .mural-header .mes-destaque {{
                    background:linear-gradient(100deg,#38bdf8 0%,#818cf8 50%,#f472b6 100%);
                    -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text;
                    /* Sem filter/drop-shadow aqui: em texto com background-clip:text
                       o filtro desenha a silhueta preta (borrada) no lugar do
                       degradê. Sem ele, o degradê aparece limpo e colorido. */
                }}
                .header-deco {{
                    display:flex; justify-content:center; gap:10px; margin-top:14px;
                    opacity:0.6; font-size:1.2rem; letter-spacing:4px;
                }}
                .header-count {{
                    margin-top:12px;
                    font-family:'Inter',sans-serif; font-size:0.82rem; font-weight:700;
                    color:#ffffff;
                    background:rgba(15,23,42,0.45);
                    border:1.5px solid rgba(255,255,255,0.4);
                    border-radius:20px; display:inline-block;
                    padding:6px 20px; letter-spacing:0.5px;
                    text-shadow:0 1px 4px rgba(0,0,0,0.55);
                    box-shadow: 0 2px 8px rgba(0,0,0,0.25);
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
                    0%, 100% {{ opacity:0.75; transform:scale(1); }}
                    50%       {{ opacity:1;    transform:scale(1.04); }}
                }}
                @keyframes boloFlutua {{
                    0%, 100% {{ transform: translateY(0) rotate(-3deg); }}
                    50%       {{ transform: translateY(-10px) rotate(3deg); }}
                }}

                /* ══ GRID ════════════════════════════════════════════════════ */
                .mural-grid {{
                    display:flex; flex-direction:column; gap:18px;
                    max-width:min(1400px,96vw); width:100%;
                }}

                /* ══ CARD BASE ═══════════════════════════════════════════════ */
                .aniversariante-row {{
                    display: grid;
                    grid-template-columns: minmax(240px,1fr) 1.6fr;
                    gap: clamp(20px,3vw,40px);
                    background: rgba(255,255,255,0.85);
                    backdrop-filter: blur(18px); -webkit-backdrop-filter: blur(18px);
                    border: 1px solid rgba(255,255,255,0.7);
                    border-radius: 22px;
                    padding: clamp(22px,2.5vw,36px) clamp(22px,3vw,40px);
                    box-shadow: 0 12px 40px rgba(0,0,0,0.15);
                    animation: fadeInUp 0.7s ease both;
                    align-items: stretch;
                    min-height: 240px; position: relative; overflow: hidden;
                    transition: transform 0.3s ease, box-shadow 0.3s ease;
                }}
                .aniversariante-row::before {{
                    content:''; position:absolute; top:0; left:0; right:0; height:4px;
                    background: linear-gradient(90deg,#38bdf8,#818cf8,#f472b6);
                    border-radius: 20px 20px 0 0;
                }}
                .aniversariante-row:hover {{
                    transform: translateY(-3px);
                    box-shadow: 0 20px 50px rgba(14,105,200,0.18), 0 6px 18px rgba(0,0,0,0.12);
                }}

                /* ══ CARD "HOJE" ═════════════════════════════════════════════ */
                .aniversariante-row.hoje {{
                    border: 2px solid rgba(251,191,36,0.8);
                    background: rgba(255,251,235,0.92);
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
                    margin-top:8px;
                    box-shadow: 0 4px 14px rgba(245,158,11,0.55), 0 1px 3px rgba(0,0,0,0.15);
                    text-shadow: 0 1px 2px rgba(120,53,15,0.25);
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
                    align-items:center; justify-content:center; padding:6px;
                    position:relative; z-index:1;
                }}
                .polaroid-wrapper {{
                    position:relative; width:100%; max-width:240px;
                    display:flex; justify-content:center;
                }}
                .polaroid-wrapper::before {{
                    content:''; position:absolute; inset:0;
                    background:rgba(0,0,0,0.08); border-radius:4px;
                    transform:rotate(4deg) translateY(6px); z-index:0;
                }}
                .polaroid {{
                    background:#ffffff; padding:14px 14px 40px; border-radius:4px;
                    box-shadow:0 16px 40px rgba(0,0,0,0.15),0 3px 10px rgba(0,0,0,0.1);
                    width:100%; color:#1e293b; text-align:center;
                    position:relative; z-index:1; transition:transform 0.45s ease;
                }}
                .polaroid::after {{
                    content:''; position:absolute; top:-14px; left:50%;
                    transform:translateX(-50%) rotate(-2deg); width:90px; height:28px;
                    background: linear-gradient(
                        135deg,
                        rgba(255,255,240,0.92) 0%,
                        rgba(230,215,180,0.55) 45%,
                        rgba(255,255,240,0.88) 100%
                    );
                    backdrop-filter:blur(4px);
                    box-shadow:0 2px 6px rgba(0,0,0,0.12), inset 0 1px 0 rgba(255,255,255,0.6);
                    border-radius:3px; z-index:5; border:1px solid rgba(200,180,130,0.3);
                }}
                .polaroid:hover {{ transform:scale(1.04) rotate(1deg); }}
                .foto-wrapper {{
                    width:100%; aspect-ratio:1/1;
                    border-radius:2px; border:1px solid #e2e8f0;
                    overflow:hidden;
                }}
                .foto-img {{
                    width:100%; height:100%;
                    object-fit:cover; object-position:center 20%;
                    display:block;
                    filter:contrast(1.02) brightness(1.02);
                }}
                .foto-placeholder {{
                    width:100%; height:100%; min-height:120px;
                    background:linear-gradient(135deg,#e0e7ff,#c7d2fe);
                    display:flex; align-items:center; justify-content:center;
                    font-family:'Playfair Display',serif; font-weight:900;
                    font-size:clamp(3rem,6vw,5rem); color:#6366f1;
                    letter-spacing:1px; text-shadow:0 2px 4px rgba(99,102,241,0.15);
                }}
                .nome {{
                    font-family:'Playfair Display',serif;
                    font-size:clamp(1.1rem,1.8vw,1.6rem);
                    font-weight:900; margin-top:12px; color:#0f172a; line-height:1.2;
                    word-break:break-word;
                    display:-webkit-box;
                    -webkit-line-clamp:2; -webkit-box-orient:vertical;
                    overflow:hidden;
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
                    font-family:'Caveat',cursive;
                    border-radius:3px 16px 3px 3px;
                    display:flex; flex-direction:column;
                    justify-content:flex-start; gap:10px; position:relative;
                    transition: transform 0.32s cubic-bezier(0.34,1.56,0.64,1),
                                box-shadow 0.28s ease;
                    cursor: pointer;
                }}
                .post-it::before {{
                    content:'📌';
                    position:absolute;
                    top:-10px;
                    right:10px;
                    left:auto;
                    transform:rotate(15deg);
                    font-size:1.1rem;
                    filter:drop-shadow(0 2px 3px rgba(0,0,0,0.2));
                }}
                .post-it:hover {{
                    transform:scale(1.09) translateY(-5px) rotate(1.5deg) !important;
                    z-index:10;
                }}
                .post-it-msg {{
                    font-size:1.2rem;
                    line-height:1.4; font-weight:700;
                    color:rgba(0,0,0,0.85); padding-top:4px; flex:1;
                    overflow:hidden; display:-webkit-box;
                    -webkit-line-clamp:5; -webkit-box-orient:vertical; word-break:break-word;
                }}
                .post-it-autor {{
                    font-size:0.95rem; font-weight:700; color:rgba(0,0,0,0.6);
                    text-align:right; margin-top:auto;
                    border-top:1px dashed rgba(0,0,0,0.15); padding-top:8px;
                    overflow:hidden; white-space:nowrap; text-overflow:ellipsis;
                }}

                .sem-recados {{
                    color:#475569; text-shadow:0 1px 3px rgba(255,255,255,0.6);
                    font-size:1.05rem; font-style:italic; padding:28px 0;
                    display:flex; align-items:center; gap:8px;
                }}
                .sem-recados-vazio {{
                    width:clamp(140px,18vw,175px);
                    min-height:130px;
                    border:2px dashed rgba(100,116,139,0.35);
                    border-radius:3px 16px 3px 3px;
                    display:flex;
                    flex-direction:column;
                    align-items:center;
                    justify-content:center;
                    gap:8px;
                    padding:16px 12px;
                    color:#94a3b8;
                    font-family:'Caveat',cursive;
                    font-size:1.15rem;
                    font-weight:700;
                    text-align:center;
                    background:rgba(248,250,252,0.5);
                    position:relative;
                    transition:border-color 0.25s ease, background 0.25s ease;
                }}
                .sem-recados-vazio:hover {{
                    border-color:rgba(14,165,233,0.45);
                    background:rgba(224,242,254,0.3);
                }}
                .sem-recados-vazio-emoji {{
                    font-size:1.6rem;
                    font-style:normal;
                    opacity:0.55;
                }}

                .sem-recados-bloqueado {{
                    background:rgba(248,250,252,0.7);
                    border:1.5px dashed rgba(100,116,139,0.35);
                    border-radius:3px 18px 3px 3px;
                    padding:20px 24px;
                    color:#475569; font-style:normal; font-weight:600;
                    letter-spacing:0.3px;
                    font-family:'Caveat',cursive;
                    font-size:1.2rem;
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

                /* ══ MODAL ═══════════════════════════════════════════════════ */
                .modal-overlay {{
                    display: none;
                    position: fixed;
                    top: 0; left: 0;
                    width: 100%; height: 100%;
                    background: rgba(0,0,0,0.5);
                    backdrop-filter: blur(8px);
                    -webkit-backdrop-filter: blur(8px);
                    z-index: 9999;
                    justify-content: center;
                    align-items: center;
                }}
                .modal-overlay.active {{ display: flex; }}
                .modal-content {{
                    background: #fffef2;
                    border-radius: 24px;
                    padding: 32px 40px;
                    max-width: 90vw; max-height: 80vh;
                    overflow-y: auto;
                    box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                    font-family: 'Caveat', cursive;
                    color: #1e293b;
                    position: relative;
                    border: 1px solid rgba(0,0,0,0.05);
                    animation: modalIn 0.3s cubic-bezier(0.34,1.56,0.64,1);
                }}
                @keyframes modalIn {{
                    from {{ opacity:0; transform: scale(0.9) translateY(20px); }}
                    to   {{ opacity:1; transform: scale(1) translateY(0); }}
                }}
                .modal-autor {{
                    text-align: right; font-size: 1.1rem; font-weight: 700;
                    color: #475569; margin-top: 16px;
                    border-top: 1px dashed rgba(0,0,0,0.15); padding-top: 12px;
                }}
                .modal-mensagem {{ font-size: 1.5rem; line-height: 1.6; color: #0f172a; }}
                .modal-close-btn {{
                    position: absolute; top: 10px; right: 16px;
                    font-size: 1.5rem; background: none; border: none;
                    cursor: pointer; color: #64748b; transition: color 0.2s;
                }}
                .modal-close-btn:hover {{ color: #0f172a; }}

                /* ══ IMPRESSÃO ═══════════════════════════════════════════════ */
                @media print {{
                    * {{ -webkit-print-color-adjust:exact !important; print-color-adjust:exact !important; }}
                    @page {{ size:A3 portrait; margin:0; }}
                    .btn-imprimir, .print-toolbar, .orientacao-badge,
                    .btn-topo {{ display:none !important; }}
                    .modal-overlay {{ display: none !important; }}
                    html, body {{
                        {estilo_fundo}
                        background-size:contain !important;
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

                /* Fundo de impressão como <img>: imprime mesmo sem a opção
                   "gráficos de segundo plano" marcada no navegador. */
                .print-bg-img {{ display: none; }}
                @media print {{
                    .print-bg-img {{
                        display: block !important;
                        position: fixed; top: 0; left: 0;
                        width: 100%; height: 100%;
                        object-fit: cover; object-position: center center;
                        z-index: -1;
                    }}
                }}

                /* Data/local do evento: visível no mural (tela) e na impressão. */
                .evento-info {{
                    margin-top: 12px;
                    display: inline-flex; flex-wrap: wrap;
                    justify-content: center; align-items: center; gap: 6px 16px;
                    font-family:'Inter',sans-serif; font-size:0.9rem; font-weight:700;
                    color:#ffffff;
                    background:rgba(15,23,42,0.45);
                    border:1px solid rgba(255,255,255,0.35);
                    border-radius:14px; padding:8px 20px;
                    letter-spacing:0.3px;
                    text-shadow:0 1px 4px rgba(0,0,0,0.55);
                }}

                @media (max-width:850px) {{
                    .aniversariante-row {{ grid-template-columns:1fr; padding:24px; }}
                }}

                /* ══ MODO TV — CARROSSEL (1 aniversariante por vez) ══════════ */
                html.tv {{ font-size: 20px; }}                 /* amplia tudo p/ ver de longe */
                html.tv body {{
                    padding: 18px 28px 28px;
                    min-height: 100vh; justify-content: flex-start;
                }}
                html.tv .mural-header {{ margin-bottom: 22px; }}
                html.tv .mural-header h1 {{ font-size: clamp(2.6rem,4.5vw,4.6rem); }}
                /* a grade vira um palco que centraliza o card ativo */
                html.tv .mural-grid {{
                    flex: 1 1 auto; display: flex; align-items: center;
                    justify-content: center; width: 100%;
                }}
                html.tv .aniversariante-row {{
                    display: none;
                    width: 100%; max-width: min(1600px, 94vw);
                    margin: 0 auto;
                }}
                html.tv .aniversariante-row.tv-active {{
                    display: grid;
                    animation: tvFade 0.7s ease both !important;
                }}
                @keyframes tvFade {{
                    from {{ opacity: 0; transform: translateY(24px) scale(0.98); }}
                    to   {{ opacity: 1; transform: none; }}
                }}
                /* indicador de posição (pontos) */
                .tv-dots {{
                    display: none; position: fixed; bottom: 22px; left: 0; right: 0;
                    justify-content: center; gap: 10px; z-index: 1000;
                }}
                html.tv .tv-dots {{ display: flex; }}
                .tv-dot {{
                    width: 12px; height: 12px; border-radius: 50%;
                    background: rgba(255,255,255,0.45);
                    border: 1px solid rgba(0,0,0,0.15);
                    transition: background 0.3s ease, transform 0.3s ease;
                }}
                .tv-dot.ativo {{
                    background: linear-gradient(135deg,#38bdf8,#f472b6);
                    transform: scale(1.35);
                }}
                /* TV: recados aparecem 1 por vez, INTEIROS, e vão passando */
                html.tv .area-post-it {{
                    justify-content: center; align-items: flex-start;
                    min-height: 240px;
                }}
                html.tv .area-post-it .post-it {{ display: none; }}
                html.tv .area-post-it .post-it.recado-ativo {{ display: flex; }}
                html.tv .post-it {{
                    width: min(620px, 94%); min-height: 220px;
                    transform: none !important;   /* sem inclinação: leitura melhor */
                    padding: 30px 28px 24px;
                }}
                html.tv .post-it-msg {{
                    -webkit-line-clamp: unset; display: block;
                    overflow: visible; font-size: 1.7rem; line-height: 1.5;
                }}
                html.tv .post-it-autor {{ font-size: 1.2rem; }}
                /* contador de recados dentro da rodada (ex.: 2/3) */
                .recado-progresso {{ display: none; }}
                html.tv .recado-progresso {{
                    display: block; text-align: center; margin-top: 14px;
                    font-family: 'Inter', sans-serif; font-size: 0.95rem;
                    font-weight: 600; color: #64748b;
                }}
            </style>
            <style id="orientacao-style">
                @media print {{ @page {{ size:A3 portrait; margin:0; }} }}
            </style>
        </head>
        <body>
            <script>
                var IS_TV = {'true' if is_tv else 'false'};

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

                // ── Carrossel do modo TV ───────────────────────────────────
                // Mostra 1 aniversariante por vez. Dentro de cada um, se houver
                // mais de um recado, eles passam um a um (inteiros). A pessoa só
                // avança depois que todos os recados foram exibidos.
                var PESSOA_MS = 10000;   // cada aniversariante fica 10s na tela;
                                         // se tiver vários recados, eles passam
                                         // dentro desses 10s (10s / nº de recados).

                function iniciarCarrosselTV() {{
                    var slides = Array.prototype.slice.call(
                        document.querySelectorAll('.aniversariante-row')
                    );
                    if (slides.length === 0) return;

                    var dotsBox = document.getElementById('tv-dots');
                    var dots = [];
                    if (dotsBox && slides.length > 1) {{
                        slides.forEach(function() {{
                            var d = document.createElement('span');
                            d.className = 'tv-dot';
                            dotsBox.appendChild(d);
                            dots.push(d);
                        }});
                    }}

                    var pIdx = 0;
                    var timer = null;

                    function recadosDe(slide) {{
                        return Array.prototype.slice.call(
                            slide.querySelectorAll('.area-post-it .post-it')
                        );
                    }}

                    function pintarRecado(recs, prog, k) {{
                        recs.forEach(function(r, i) {{
                            r.classList.toggle('recado-ativo', i === k);
                        }});
                        if (prog && recs.length > 1) {{
                            prog.textContent = '💬 recado ' + (k + 1) + ' de ' + recs.length;
                        }} else if (prog) {{
                            prog.textContent = '';
                        }}
                    }}

                    function proximaPessoa() {{
                        if (timer) {{ clearTimeout(timer); clearInterval(timer); timer = null; }}
                        ativarPessoa((pIdx + 1) % slides.length);
                    }}

                    function ativarPessoa(i) {{
                        if (timer) {{ clearTimeout(timer); clearInterval(timer); timer = null; }}
                        slides.forEach(function(s, j) {{ s.classList.toggle('tv-active', j === i); }});
                        dots.forEach(function(d, j) {{ d.classList.toggle('ativo', j === i); }});
                        pIdx = i;
                        window.scrollTo(0, 0);

                        var slide = slides[i];
                        var recs  = recadosDe(slide);
                        var prog  = slide.querySelector('.recado-progresso');

                        if (recs.length > 1) {{
                            // divide os 10s entre os recados, passando um a um
                            var porRecado = PESSOA_MS / recs.length;
                            var k = 0;
                            pintarRecado(recs, prog, 0);
                            timer = setInterval(function() {{
                                k++;
                                if (k >= recs.length) {{ proximaPessoa(); return; }}
                                pintarRecado(recs, prog, k);
                            }}, porRecado);
                        }} else {{
                            pintarRecado(recs, prog, 0);   // 0 ou 1 recado
                            timer = setTimeout(proximaPessoa, PESSOA_MS);
                        }}
                    }}

                    ativarPessoa(0);
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

                        iniciarCarrosselTV();

                        setTimeout(function() {{
                            try {{ window.parent.location.reload(); }}
                            catch(e) {{ window.location.reload(); }}
                        }}, 300000);
                    }}
                }});
            </script>

            {fundo_print_img}
            <div id="badge-orientacao" class="orientacao-badge"></div>
            <div id="tv-dots" class="tv-dots"></div>
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
                    <div class="header-count">
                        {'🎂 1 aniversariante' if total_mes == 1 else f'🎂 {total_mes} aniversariantes'}
                        {' — incluindo hoje! 🥳' if mes_atual == hoje.month and any(df_mes["data_nascimento"].dt.day == dia_atual) else ''}
                    </div>
                    {evento_html}
                </div>
            </div>

            <div class="mural-grid">
        """

        cartoes_html = ""

        for idx, (_, row) in enumerate(df_mes.iterrows()):
            nome_raw = str(row.get("nome", "Sem nome")).strip()
            nome_formatado = nome_raw.title()
            nome           = html_lib.escape(nome_formatado)

            # ══ TRATAMENTO DE CURIOSIDADE (EVITA "nan") ══════════════════════
            curiosidade_raw = str(row.get("curiosidade", "")).strip()
            if curiosidade_raw.lower() in ("", "nan", "none", "null"):
                texto_curiosidade = ""
            else:
                texto_curiosidade = html_lib.escape(curiosidade_raw)

            dia = row["data_nascimento"].day if pd.notna(row["data_nascimento"]) else "?"

            partes        = nome_formatado.split()
            primeiro_nome = partes[0] if partes else nome_formatado

            # Iniciais para o placeholder (em vez da silhueta genérica)
            if len(partes) >= 2:
                iniciais = (partes[0][0] + partes[-1][0]).upper()
            elif partes:
                iniciais = partes[0][:2].upper()
            else:
                iniciais = "?"
            iniciais = html_lib.escape(iniciais)

            img_url = str(row.get("foto_url", "")).strip().replace("'", "%27").replace('"', "%22")
            if img_url:
                foto_html = f'''
                <div class="foto-wrapper">
                    <img class="foto-img" src="{img_url}"
                         onerror="this.style.display='none';this.nextElementSibling.style.display='flex';"
                         alt="Foto de {nome}" />
                    <div class="foto-placeholder" style="display:none;">{iniciais}</div>
                </div>'''
            else:
                foto_html = f'<div class="foto-wrapper"><div class="foto-placeholder">{iniciais}</div></div>'

            curiosidade_html = ""
            if texto_curiosidade:
                curiosidade_html = f'<div class="curiosidade-txt">\"{texto_curiosidade}\"</div>'

            e_hoje     = (dia == dia_atual_efetivo)
            classe_row = "aniversariante-row hoje" if e_hoje else "aniversariante-row"
            badge_hoje = '<div class="badge-hoje">🎂 Hoje é o grande dia! 🎉</div>' if e_hoje else ""

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
                    post_its_html = """
                    <div class="sem-recados-vazio">
                        <span class="sem-recados-vazio-emoji">📌</span>
                        Seja o primeiro a deixar um recado!
                    </div>"""
                else:
                    for i, (_, recado) in enumerate(recados_pessoa.iterrows()):
                        mensagem_raw = str(recado.get("mensagem", "")).strip()
                        mensagem = html_lib.escape(mensagem_raw)
                        autor_raw = str(recado.get("de_quem", "Anônimo")).strip()
                        autor = html_lib.escape(autor_raw.title()) if autor_raw else "Anônimo"

                        # Hash determinístico: a rotação fica estável entre
                        # execuções (hash() do Python varia por PYTHONHASHSEED).
                        seed_bytes = (mensagem + autor + nome).encode("utf-8")
                        seed_val   = int.from_bytes(
                            hashlib.md5(seed_bytes).digest()[:4], "big"
                        )
                        rotacao    = (seed_val % 9) - 4

                        cor = POSTIT_COLORS[i % len(POSTIT_COLORS)]

                        post_its_html += f"""
                        <div class="post-it"
                             style="background-color:{cor['bg']};
                                    transform:rotate({rotacao}deg);
                                    box-shadow:4px 6px 15px {cor['shadow']},0 1px 3px rgba(0,0,0,0.06);"
                             data-mensagem="{html_lib.escape(mensagem_raw)}"
                             data-autor="{html_lib.escape(autor_raw)}">
                            <div class="post-it-msg">{mensagem}</div>
                            <div class="post-it-autor">~ {autor}</div>
                        </div>
                        """
            else:
                post_its_html = """
                <div class="sem-recados-vazio">
                    <span class="sem-recados-vazio-emoji">📌</span>
                    Seja o primeiro a deixar um recado!
                </div>"""

            badge_contagem = ""
            if n_recados_pessoa > 0:
                label = "recado" if n_recados_pessoa == 1 else "recados"
                badge_contagem = (
                    f'<span class="badge-contagem">💬 {n_recados_pessoa} {label}</span>'
                )

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
                    <div class="recado-progresso"></div>
                </div>
            </div>
            """

        modal_html = """
            </div>

            <div id="modal-overlay" class="modal-overlay">
                <div class="modal-content">
                    <button id="modal-close-btn" class="modal-close-btn">&times;</button>
                    <div id="modal-mensagem" class="modal-mensagem"></div>
                    <div id="modal-autor" class="modal-autor"></div>
                </div>
            </div>

            <script>
                document.addEventListener('DOMContentLoaded', function() {
                    var overlay = document.getElementById('modal-overlay');
                    var modalMensagem = document.getElementById('modal-mensagem');
                    var modalAutor = document.getElementById('modal-autor');

                    function abrirModal(texto, autor) {
                        modalMensagem.textContent = texto;
                        modalAutor.textContent = '~ ' + (autor || 'Anônimo');
                        overlay.classList.add('active');
                    }

                    function fecharModal() {
                        overlay.classList.remove('active');
                    }

                    overlay.addEventListener('click', function(e) {
                        if (e.target === overlay) { fecharModal(); }
                    });

                    document.getElementById('modal-close-btn').addEventListener('click', fecharModal);

                    document.addEventListener('click', function(e) {
                        var postit = e.target.closest('.post-it');
                        if (postit) {
                            var msg = postit.dataset.mensagem;
                            var autor = postit.dataset.autor;
                            if (msg !== undefined) {
                                abrirModal(msg, autor || 'Anônimo');
                            }
                        }
                    });
                });
            </script>
        """

        full_html = html_base + cartoes_html + modal_html + "</body></html>"
        if is_tv:
            # No carrossel, só um card aparece por vez: altura fixa de "telão"
            # e sem barra de rolagem interna.
            components.html(full_html, height=1024, scrolling=False)
        else:
            components.html(full_html, height=altura_iframe, scrolling=True)

    else:
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
                    background-size:cover; background-position:center center;
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
                @keyframes boloFlutua {{
                    0%, 100% {{ transform: translateY(0) rotate(-3deg); }}
                    50%       {{ transform: translateY(-12px) rotate(3deg); }}
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
                .empty-emoji {{
                    font-size:4rem; margin-bottom:20px; display:inline-block;
                    animation: boloFlutua 3s ease-in-out infinite;
                }}
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

    # ── SUB-MURAL RETROATIVO (meses 1,2,3) – Abril/2026 ────────────────────
    if mes_atual == 4 and hoje.year == 2026:
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
                    background-position: center center !important;
                    background-repeat: no-repeat !important;
                    min-height: 100%;
                }}
                body {{
                    background: transparent !important;
                    display: flex; align-items: center; justify-content: center;
                    min-height: 100vh; padding: 20px;
                }}
                .sub-mural-container {{
                    background: rgba(255,255,255,0.5);
                    backdrop-filter: blur(8px); -webkit-backdrop-filter: blur(8px);
                    border: 1px solid rgba(255,255,255,0.5); border-radius: 18px;
                    padding: 28px 24px 24px; margin: 0 auto;
                    max-width: min(1400px, 96vw); text-align: center;
                    box-shadow: 0 4px 20px rgba(0,0,0,0.08);
                    position: relative; overflow: hidden;
                }}
                .sub-mural-container::before {{
                    content: ''; position: absolute; top: 0; left: 0; right: 0; height: 3px;
                    background: linear-gradient(90deg, #38bdf8, #818cf8, #f472b6);
                    border-radius: 18px 18px 0 0;
                }}
                .sub-mural-titulo {{
                    font-family: 'Playfair Display', serif; font-size: 1.35rem; font-weight: 700;
                    margin-bottom: 20px;
                    background: linear-gradient(100deg, #0284c7 0%, #818cf8 60%, #f472b6 100%);
                    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
                    background-clip: text; display: inline-block;
                }}
                .sub-mural-grid {{
                    display: flex; flex-wrap: wrap; gap: 20px; justify-content: center;
                }}
                .mini-polaroid {{
                    background: #fff; padding: 10px 10px 14px; border-radius: 4px;
                    box-shadow: 0 6px 16px rgba(0,0,0,0.1); width: 138px; text-align: center;
                    transition: transform 0.25s cubic-bezier(0.34,1.56,0.64,1), box-shadow 0.25s ease;
                }}
                .mini-polaroid:hover {{
                    transform: scale(1.07) translateY(-3px);
                    box-shadow: 0 12px 24px rgba(14,105,200,0.15);
                }}
                .mini-foto {{
                    width: 100%; aspect-ratio: 1; overflow: hidden;
                    border-radius: 2px; margin-bottom: 6px;
                }}
                .mini-foto img {{ width: 100%; height: 100%; object-fit: cover; display: block; }}
                .mini-nome {{
                    font-family: 'Inter', sans-serif; font-size: 0.75rem; font-weight: 600;
                    color: #1e293b; line-height: 1.2; word-break: break-word;
                    overflow-wrap: break-word; white-space: normal; overflow: hidden;
                    display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical;
                }}
                .mini-data {{ font-family: 'Inter', sans-serif; font-size: 0.65rem; color: #64748b; margin-top: 3px; }}
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

else:
    st.warning("⚠️ Nenhum dado encontrado no banco de dados.")
