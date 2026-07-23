import uuid
import streamlit as st
import pandas as pd
from utils import get_supabase

st.set_page_config(page_title="Fotos para Link", page_icon="🔗")

BUCKET = "fotos_mural"

supabase = get_supabase()

st.title("🔗 Fotos para Link")
st.write(
    "Transforme fotos em **links** para colar na planilha. Arraste as imagens, "
    "clique em **Gerar links** e copie as URLs (ou baixe tudo em CSV). "
    "As fotos são hospedadas no mesmo lugar usado pelo Mural."
)

# ── Acesso restrito (mesma senha do painel admin, se configurada) ─────────────
SENHA_CORRETA = st.secrets.get("ADMIN_PASSWORD", "")
if SENHA_CORRETA:
    senha = st.text_input("🔒 Senha de administrador", type="password")
    if senha != SENHA_CORRETA:
        if senha:
            st.error("Senha incorreta.")
        else:
            st.info("Digite a senha de administrador para usar esta ferramenta.")
        st.stop()


def enviar_foto(arquivo) -> str:
    """Sobe o arquivo para o Storage e devolve a URL pública."""
    ext = arquivo.name.split(".")[-1].lower()
    nome_arq = f"{uuid.uuid4()}.{ext}"
    conteudo = arquivo.getvalue()
    try:
        supabase.storage.from_(BUCKET).upload(
            nome_arq, conteudo, {"content-type": arquivo.type or "image/jpeg"}
        )
    except Exception:
        # Retrocompatível com versões do client que não aceitam file_options.
        supabase.storage.from_(BUCKET).upload(nome_arq, conteudo)
    return supabase.storage.from_(BUCKET).get_public_url(nome_arq)


arquivos = st.file_uploader(
    "Fotos (pode selecionar várias)",
    type=["jpg", "jpeg", "png"],
    accept_multiple_files=True,
)

if arquivos:
    st.caption(f"{len(arquivos)} foto(s) selecionada(s).")
    if st.button("🚀 Gerar links", type="primary"):
        resultados = []
        barra = st.progress(0.0)
        for i, arq in enumerate(arquivos):
            nome_base = arq.name.rsplit(".", 1)[0]
            try:
                url = enviar_foto(arq)
                resultados.append({"nome": nome_base, "link": url, "ok": True})
            except Exception as e:
                resultados.append({"nome": nome_base, "link": f"ERRO: {e}", "ok": False})
            barra.progress((i + 1) / len(arquivos))
        st.session_state["resultados_links"] = resultados

# ── Resultados ────────────────────────────────────────────────────────────────
resultados = st.session_state.get("resultados_links")
if resultados:
    st.divider()
    ok = [r for r in resultados if r["ok"]]
    falhas = [r for r in resultados if not r["ok"]]

    if ok:
        st.success(f"✅ {len(ok)} link(s) gerado(s)!")
    if falhas:
        st.error(f"⚠️ {len(falhas)} foto(s) falharam. Veja abaixo.")

    df = pd.DataFrame([{"nome": r["nome"], "link": r["link"]} for r in resultados])

    st.write("**Tabela (nome + link)** — copie ou baixe para a planilha:")
    st.dataframe(df, use_container_width=True, hide_index=True)

    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇️ Baixar CSV (nome, link)",
        data=csv,
        file_name="fotos_links.csv",
        mime="text/csv",
        use_container_width=True,
    )

    st.write("**Links individuais** (clique no ícone de copiar em cada um):")
    for r in ok:
        st.caption(r["nome"])
        st.code(r["link"], language=None)
        st.image(r["link"], width=110)

st.info(
    "💡 Dica: o nome que aparece na tabela vem do nome do arquivo da foto. "
    "Renomeie os arquivos com o nome da pessoa antes de subir para já sair "
    "certinho na planilha. Depois, é só colar a coluna **link** na coluna "
    "`foto_url` da sua base."
)
