import streamlit as st
import pandas as pd
from datetime import datetime
import html as html_lib
from utils import get_supabase, carregar_config

st.set_page_config(page_title="Colaboradores", layout="wide", page_icon="👥")

# ──────────────────────────────────────────────────────────────────────────────
# Conexão e cache (idêntico ao app principal, mantido aqui por independência)
# ──────────────────────────────────────────────────────────────────────────────
supabase = get_supabase()
config   = carregar_config()

@st.cache_data(ttl=120)
def carregar_aniversariantes(_supabase):
    return _supabase.table("aniversariantes").select("*").execute().data or []

# ──────────────────────────────────────────────────────────────────────────────
# Estilos visuais consistentes com o mural
# ──────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .colab-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
        gap: 24px;
        padding: 16px 0;
    }
    .colab-card {
        background: rgba(255, 255, 255, 0.75);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border-radius: 8px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.1);
        padding: 14px 14px 20px;
        text-align: center;
        transition: transform 0.2s, box-shadow 0.2s;
        border: 1px solid rgba(255,255,255,0.5);
    }
    .colab-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 16px 35px rgba(0,0,0,0.15);
    }
    .colab-foto {
        width: 100%;
        aspect-ratio: 1 / 1;
        object-fit: cover;
        border-radius: 4px;
        border: 1px solid #e2e8f0;
        display: block;
    }
    .foto-placeholder {
        width: 100%;
        aspect-ratio: 1 / 1;
        background: linear-gradient(135deg, #f1f5f9, #cbd5e1);
        border-radius: 4px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 4rem;
    }
    .colab-nome {
        font-family: 'Playfair Display', serif;
        font-size: 1.15rem;
        font-weight: 700;
        color: #0f172a;
        margin-top: 12px;
        line-height: 1.2;
        word-break: break-word;
    }
    .colab-data {
        font-family: 'Inter', sans-serif;
        font-size: 0.8rem;
        color: #0284c7;
        font-weight: 600;
        margin-top: 6px;
        letter-spacing: 0.5px;
    }
    .mes-header {
        font-family: 'Playfair Display', serif;
        font-size: 1.8rem;
        font-weight: 700;
        color: #1e293b;
        border-bottom: 2px solid #e2e8f0;
        padding-bottom: 6px;
        margin: 32px 0 16px;
    }
    .sem-dados {
        text-align: center;
        font-family: 'Inter', sans-serif;
        color: #64748b;
        font-size: 1.2rem;
        margin-top: 60px;
    }
    .contador {
        font-family: 'Inter', sans-serif;
        font-size: 0.9rem;
        color: #475569;
        margin-bottom: 16px;
    }
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────────────────
# Carregamento dos dados
# ──────────────────────────────────────────────────────────────────────────────
st.title("👥 Colaboradores")
st.caption("Todos os membros registrados na nossa comunidade.")

with st.spinner("Carregando colaboradores..."):
    dados = carregar_aniversariantes(supabase)

if not dados:
    st.markdown('<p class="sem-dados">Nenhum colaborador cadastrado ainda.</p>', unsafe_allow_html=True)
    st.stop()

# ──────────────────────────────────────────────────────────────────────────────
# Processamento seguro
# ──────────────────────────────────────────────────────────────────────────────
df = pd.DataFrame(dados)
df["data_nascimento"] = pd.to_datetime(df["data_nascimento"], errors="coerce")

df_com_data = df.dropna(subset=["data_nascimento"]).copy()
df_sem_data = df[df["data_nascimento"].isna()].copy()

df_com_data["mes"] = df_com_data["data_nascimento"].dt.month
df_com_data["dia"]  = df_com_data["data_nascimento"].dt.day
df_com_data = df_com_data.sort_values(["mes", "dia"])

MESES_PTBR = {
    1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril",
    5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto",
    9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
}

def foto_valida(url):
    if not url:
        return False
    url_str = str(url).strip()
    return url_str.lower() not in ("nan", "none", "null", "")

total_colaboradores = len(df)
st.markdown(f'<div class="contador">📋 Total de colaboradores: {total_colaboradores}</div>', unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────────────────
# Construção dos cards por mês (sem concatenar strings com +, evitando tags)
# ──────────────────────────────────────────────────────────────────────────────
for mes, grupo in df_com_data.groupby("mes"):
    nome_mes = MESES_PTBR.get(int(mes), "Mês desconhecido")
    st.markdown(f'<div class="mes-header">{nome_mes}</div>', unsafe_allow_html=True)

    cards = []
    for _, row in grupo.iterrows():
        nome_raw = str(row.get("nome", "Sem nome")).strip()
        nome = html_lib.escape(nome_raw.title())
        dia = int(row["dia"])
        img_url = str(row.get("foto_url", "")).strip()

        if foto_valida(img_url):
            img_url_clean = img_url.replace("'", "%27").replace('"', "%22")
            foto_bloco = f'<img class="colab-foto" src="{img_url_clean}" alt="Foto de {nome}" />'
        else:
            foto_bloco = '<div class="foto-placeholder">👤</div>'

        card = (
            '<div class="colab-card">'
            f'{foto_bloco}'
            f'<div class="colab-nome">{nome}</div>'
            f'<div class="colab-data">🎂 {dia} de {nome_mes}</div>'
            '</div>'
        )
        cards.append(card)

    grid = '<div class="colab-grid">' + '\n'.join(cards) + '</div>'
    st.markdown(grid, unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────────────────
# Colaboradores sem data
# ──────────────────────────────────────────────────────────────────────────────
if not df_sem_data.empty:
    st.markdown('<div class="mes-header">Sem data definida</div>', unsafe_allow_html=True)

    cards = []
    for _, row in df_sem_data.iterrows():
        nome_raw = str(row.get("nome", "Sem nome")).strip()
        nome = html_lib.escape(nome_raw.title())
        img_url = str(row.get("foto_url", "")).strip()

        if foto_valida(img_url):
            img_url_clean = img_url.replace("'", "%27").replace('"', "%22")
            foto_bloco = f'<img class="colab-foto" src="{img_url_clean}" alt="Foto de {nome}" />'
        else:
            foto_bloco = '<div class="foto-placeholder">👤</div>'

        card = (
            '<div class="colab-card">'
            f'{foto_bloco}'
            f'<div class="colab-nome">{nome}</div>'
            '<div class="colab-data">🎂 Data não informada</div>'
            '</div>'
        )
        cards.append(card)

    grid = '<div class="colab-grid">' + '\n'.join(cards) + '</div>'
    st.markdown(grid, unsafe_allow_html=True)

st.markdown("---")
st.caption("Dados atualizados automaticamente a cada 2 minutos.")
