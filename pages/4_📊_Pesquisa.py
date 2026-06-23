import streamlit as st
from utils import get_supabase, carregar_config, to_bool
import pandas as pd
import json
from datetime import datetime

st.set_page_config(page_title="Pesquisa de Satisfação", page_icon="📊", layout="centered")

supabase = get_supabase()
config   = carregar_config()

liberar_pesquisa = to_bool(config.get("liberar_pesquisa", True))

# ── ADMIN ─────────────────────────────────────────────────────────────────────
SENHA_CORRETA  = st.secrets.get("ADMIN_PASSWORD", "")
senha_digitada = st.sidebar.text_input("Acesso restrito", type="password")
modo_admin     = bool(SENHA_CORRETA) and (senha_digitada == SENHA_CORRETA)

if modo_admin:
    st.sidebar.success("Modo Admin Ativado! 🔓")
    novo_estado = st.sidebar.checkbox("Pesquisa aberta", value=liberar_pesquisa)
    if st.sidebar.button("💾 Guardar"):
        try:
            busca = supabase.table("configuracoes_mural").select("id").eq("chave", "liberar_pesquisa").execute()
            if busca.data:
                supabase.table("configuracoes_mural").update({"valor": str(novo_estado)}).eq("chave", "liberar_pesquisa").execute()
            else:
                supabase.table("configuracoes_mural").insert({"chave": "liberar_pesquisa", "valor": str(novo_estado)}).execute()
            st.sidebar.success("Salvo!")
            st.rerun()
        except Exception as e:
            st.sidebar.error(f"Erro: {e}")

    # ── PAINEL DE RESULTADOS (apenas admin) ───────────────────────────────────
    st.title("📊 Resultados da Pesquisa")
    try:
        dados = supabase.table("pesquisa_satisfacao").select("*").execute().data or []
        if not dados:
            st.info("Ainda não há respostas.")
            st.stop()

        df = pd.DataFrame(dados)
        df["criado_em"] = pd.to_datetime(df["criado_em"])

        SECOES = {
            "comida":    "🍽️ Comida e Cardápio",
            "decoracao": "🎨 Decoração",
            "mural":     "🎂 Mural de Aniversariantes",
            "recados":   "💌 Sistema de Recados",
            "organizacao": "📋 Organização Geral",
            "comunicacao": "📢 Comunicação e Avisos",
        }

        st.metric("Total de Respostas", len(df))
        st.divider()

        # Médias por categoria
        st.subheader("⭐ Médias por Categoria")
        cols = st.columns(3)
        for i, (chave, label) in enumerate(SECOES.items()):
            col_nota = f"nota_{chave}"
            if col_nota in df.columns:
                vals = pd.to_numeric(df[col_nota], errors="coerce").dropna()
                if not vals.empty:
                    cols[i % 3].metric(label, f"{vals.mean():.1f} / 5 ({'⭐' * round(vals.mean())})")

        st.divider()

        # Sugestões por categoria
        st.subheader("💬 Sugestões Recebidas")
        for chave, label in SECOES.items():
            col_sug = f"sug_{chave}"
            if col_sug in df.columns:
                sugestoes = df[df[col_sug].notna() & (df[col_sug].str.strip() != "")][[col_sug, "criado_em"]]
                if not sugestoes.empty:
                    with st.expander(f"{label} — {len(sugestoes)} sugestão(ões)"):
                        for _, row in sugestoes.iterrows():
                            st.markdown(f"> {row[col_sug]}")
                            st.caption(row["criado_em"].strftime("%d/%m/%Y %H:%M"))

        # Comentário geral
        if "comentario_geral" in df.columns:
            gerais = df[df["comentario_geral"].notna() & (df["comentario_geral"].str.strip() != "")]
            if not gerais.empty:
                with st.expander(f"🗒️ Comentários Gerais — {len(gerais)}"):
                    for _, row in gerais.iterrows():
                        st.markdown(f"> {row['comentario_geral']}")
                        st.caption(row["criado_em"].strftime("%d/%m/%Y %H:%M"))

        st.divider()
        # Tabela completa exportável
        with st.expander("📥 Ver Tabela Completa"):
            st.dataframe(df.drop(columns=["id"], errors="ignore"), use_container_width=True)

    except Exception as e:
        st.error(f"Erro ao carregar resultados: {e}")

    st.stop()

# ── PORTEIRO ──────────────────────────────────────────────────────────────────
if not liberar_pesquisa:
    st.title("📊 Pesquisa de Satisfação")
    st.info("🔒 A pesquisa ainda não está disponível. Fique atento às comunicações da GAFI!")
    st.stop()

# ── FORMULÁRIO PÚBLICO ────────────────────────────────────────────────────────
st.title("📊 Pesquisa de Satisfação")
st.markdown("""
Sua opinião é essencial para melhorarmos cada vez mais as celebrações da GAFI! 🎉  
Avalie cada item e deixe sugestões — leva menos de **2 minutos**.
""")

SECOES_FORM = [
    {
        "chave": "comida",
        "emoji": "🍽️",
        "titulo": "Comida e Cardápio",
        "descricao": "Variedade, sabor, quantidade e apresentação dos alimentos servidos.",
        "placeholder": "Ex: Adorei o bolo! Sugiro incluir opção sem glúten na próxima edição...",
    },
    {
        "chave": "decoracao",
        "emoji": "🎨",
        "titulo": "Decoração",
        "descricao": "Ambientação, cores, balões, arranjos e visual geral do espaço.",
        "placeholder": "Ex: A decoração ficou linda! Poderia ter mais balões coloridos...",
    },
    {
        "chave": "mural",
        "emoji": "🎂",
        "titulo": "Mural de Aniversariantes",
        "descricao": "Design, fotos, informações exibidas e experiência visual do mural.",
        "placeholder": "Ex: Ficou muito bonito! Seria legal ter a data de aniversário mais em destaque...",
    },
    {
        "chave": "recados",
        "emoji": "💌",
        "titulo": "Sistema de Recados",
        "descricao": "Facilidade para deixar e visualizar mensagens para os aniversariantes.",
        "placeholder": "Ex: Achei fácil de usar! Gostaria de poder adicionar emojis nos recados...",
    },
    {
        "chave": "organizacao",
        "emoji": "📋",
        "titulo": "Organização Geral",
        "descricao": "Pontualidade, logística, espaço e condução do evento.",
        "placeholder": "Ex: Tudo muito bem organizado! Seria ótimo ter um momento para fotos em grupo...",
    },
    {
        "chave": "comunicacao",
        "emoji": "📢",
        "titulo": "Comunicação e Avisos",
        "descricao": "Clareza e antecedência dos comunicados sobre o evento.",
        "placeholder": "Ex: Fiquei sabendo em cima da hora. Um aviso com mais dias de antecedência ajudaria...",
    },
]

NOTAS_LABEL = {
    1: "😞 Muito Fraco",
    2: "😕 Fraco",
    3: "😐 Regular",
    4: "🙂 Bom",
    5: "😃 Excelente",
}

respostas = {}

with st.form("pesquisa_satisfacao_form", clear_on_submit=True):

    for secao in SECOES_FORM:
        chave = secao["chave"]
        st.subheader(f"{secao['emoji']} {secao['titulo']}")
        st.caption(secao["descricao"])

        nota = st.select_slider(
            f"Avaliação — {secao['titulo']}",
            options=[1, 2, 3, 4, 5],
            value=5,
            format_func=lambda n: NOTAS_LABEL[n],
            key=f"nota_{chave}",
            label_visibility="collapsed",
        )
        respostas[f"nota_{chave}"] = nota

        sugestao = st.text_area(
            f"Sugestão para {secao['titulo']} (opcional)",
            placeholder=secao["placeholder"],
            max_chars=400,
            key=f"sug_{chave}",
            label_visibility="collapsed",
        )
        respostas[f"sug_{chave}"] = sugestao.strip() if sugestao else None

        st.divider()

    st.subheader("🗒️ Comentário Geral")
    st.caption("Algo que não se encaixa nos itens acima? Fique à vontade!")
    comentario_geral = st.text_area(
        "Comentário geral",
        placeholder="Escreva o que quiser — elogios, críticas, sugestões livres...",
        max_chars=600,
        key="comentario_geral",
        label_visibility="collapsed",
    )

    st.write("")
    enviado = st.form_submit_button(
        "📨 Enviar Pesquisa",
        type="primary",
        use_container_width=True,
    )

if enviado:
    payload = {k: v for k, v in respostas.items() if v is not None}
    payload["comentario_geral"] = comentario_geral.strip() if comentario_geral else None

    try:
        supabase.table("pesquisa_satisfacao").insert(payload).execute()
        st.success("✅ Obrigado pelo seu feedback! Cada sugestão ajuda a GAFI a melhorar. 💛")
        st.balloons()
    except Exception as e:
        st.error(f"Erro ao enviar: {e}")
