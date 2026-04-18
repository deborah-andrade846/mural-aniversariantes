import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
from datetime import datetime
from supabase import create_client, Client
import random
import base64
import re

st.set_page_config(page_title="Mural de Clima", layout="wide", page_icon="🎉")

# --- MODO TV (TELA LIMPA) ---
# Se a URL terminar com ?tv=true, esconde toda a interface padrão do Streamlit
is_tv = st.query_params.get("tv") == "true"

if is_tv:
    st.markdown("""
        <style>
            /* Esconde o cabeçalho (header), menu principal e rodapé */
            header {visibility: hidden;}
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            
            /* Esconde a setinha de abrir a sidebar */
            [data-testid="collapsedControl"] {display: none;}
            
            /* Remove as margens e o padding superior padrão do Streamlit */
            .block-container {
                padding-top: 0rem !important;
                padding-bottom: 0rem !important;
                max-width: 100% !important;
            }
        </style>
    """, unsafe_allow_html=True)

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

def cor_hex_valida(valor):
    return isinstance(valor, str) and bool(re.fullmatch(r"#[0-9a-fA-F]{6}", valor.strip()))

config = carregar_config()

exibir_mural    = to_bool(config.get("exibir_mural",    False))
liberar_recados = to_bool(config.get("liberar_recados", False))
liberar_cadastro = to_bool(config.get("liberar_cadastro", True))

# --- 3. ADMIN ---
st.sidebar.title("⚙️ Administração CGC")
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
            f"background-size: cover; background-position: center; background-attachment: fixed;"
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
            f"background-size: cover; background-position: center; background-attachment: fixed;"
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
            f"background-size: cover; background-position: center; background-attachment: fixed;"
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
            {estilo_fundo}
        }}
        .porteiro-card {{
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 16px;
            padding: 50px 30px;
            text-align: center;
            max-width: 600px;
            margin: 10vh auto;
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
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
            text-shadow: 0 2px 4px rgba(0,0,0,0.5);
        }}
        .porteiro-texto {{
            font-family: 'Lato', sans-serif;
            font-size: 1.1rem;
            line-height: 1.6;
            color: #e2e8f0;
            text-shadow: 0 1px 3px rgba(0,0,0,0.5);
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
            A equipe da CGC está cuidando de cada detalhe com muito carinho!<br><br>
            Fique atento às comunicações internas para a grande revelação do nosso quadro de aniversariantes.
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
                    padding: 60px 20px;
                    min-height: 100vh;
                }}
                /* ── Header ── */
                .mural-header {{
                    text-align: center;
                    margin-bottom: 70px;
                    background: rgba(0, 0, 0, 0.4);
                    padding: 30px 60px;
                    border-radius: 20px;
                    backdrop-filter: blur(10px);
                    border: 1px solid rgba(255, 255, 255, 0.1);
                    box-shadow: 0 10px 30px rgba(0,0,0,0.3);
                }}
                .mural-header .subtitulo {{
                    font-weight: 400;
                    font-size: 1.1rem;
                    letter-spacing: 6px;
                    text-transform: uppercase;
                    color: #e2e8f0;
                    margin-bottom: 10px;
                }}
                .mural-header h1 {{
                    font-family: 'Playfair Display', serif;
                    font-size: 3.5rem;
                    font-weight: 900;
                    color: #ffffff;
                    text-shadow: 0 4px 15px rgba(0,0,0,0.5);
                    line-height: 1.2;
                }}
                .mural-header .mes-destaque {{
                    color: #38bdf8;
                    background: linear-gradient(90deg, #38bdf8, #818cf8);
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                }}
                
                /* ── Grid Principal da Tela (Web/TV) ── */
                .mural-grid {{
                    display: flex;
                    flex-direction: column;
                    gap: 40px;
                    max-width: 1200px;
                    width: 100%;
                }}

                /* ── Bloco de Celebração (Web/TV Horizontal) ── */
                .aniversariante-row {{
                    display: flex;
                    flex-direction: row;
                    gap: 40px;
                    background: rgba(255, 255, 255, 0.08);
                    backdrop-filter: blur(16px);
                    -webkit-backdrop-filter: blur(16px);
                    border: 1px solid rgba(255, 255, 255, 0.2);
                    border-radius: 24px;
                    padding: 40px;
                    box-shadow: 0 15px 35px rgba(0,0,0,0.2);
                    animation: fadeInUp 0.8s ease both;
                    align-items: center;
                }}
                @media (max-width: 800px) {{
                    .aniversariante-row {{
                        flex-direction: column;
                        padding: 25px;
                    }}
                }}

                @keyframes fadeInUp {{
                    from {{ opacity: 0; transform: translateY(30px); }}
                    to   {{ opacity: 1; transform: translateY(0); }}
                }}

                /* ── Polaroid ── */
                .polaroid-container {{
                    flex-shrink: 0;
                    position: relative;
                }}
                .polaroid {{
                    background: #ffffff;
                    padding: 16px 16px 50px;
                    border-radius: 4px;
                    box-shadow: 
                        0 10px 20px rgba(0,0,0,0.3),
                        inset 0 1px 0 rgba(255,255,255,1);
                    width: 260px;
                    color: #1e293b;
                    text-align: center;
                    position: relative;
                    transition: transform 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
                }}
                .polaroid::after {{
                    content: '';
                    position: absolute;
                    top: -12px;
                    left: 50%;
                    transform: translateX(-50%) rotate(-3deg);
                    width: 100px;
                    height: 30px;
                    background-color: rgba(255, 255, 255, 0.4);
                    backdrop-filter: blur(4px);
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    border-radius: 2px;
                    z-index: 5;
                    border: 1px solid rgba(255,255,255,0.5);
                }}
                .polaroid:hover {{
                    transform: scale(1.05) rotate(2deg);
                }}
                .foto {{
                    width: 100%;
                    height: 230px;
                    background-size: cover;
                    background-position: center 20%;
                    border-radius: 2px;
                    border: 1px solid #cbd5e1;
                    filter: contrast(1.05) brightness(1.02);
                }}
                .foto-placeholder {{
                    width: 100%;
                    height: 230px;
                    background: linear-gradient(135deg, #f1f5f9, #cbd5e1);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-size: 5rem;
                }}
                .nome {{
                    font-family: 'Playfair Display', serif;
                    font-size: 1.4rem;
                    font-weight: 900;
                    margin-top: 15px;
                    color: #0f172a;
                }}
                .data-badge {{
                    display: inline-block;
                    background: #1e293b;
                    color: #fff;
                    font-size: 0.8rem;
                    font-weight: 700;
                    letter-spacing: 1px;
                    text-transform: uppercase;
                    padding: 4px 12px;
                    border-radius: 20px;
                    margin-top: 8px;
                }}

                /* ── Área de Post-its ── */
                .recados-section {{
                    flex-grow: 1;
                    display: flex;
                    flex-direction: column;
                    justify-content: center;
                }}
                .recados-titulo {{
                    font-family: 'Playfair Display', serif;
                    font-size: 1.8rem;
                    color: #ffffff;
                    margin-bottom: 20px;
                    border-bottom: 2px solid rgba(255,255,255,0.2);
                    padding-bottom: 10px;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                }}
                .area-post-it {{
                    display: flex;
                    flex-wrap: wrap;
                    gap: 20px;
                    justify-content: flex-start;
                }}
                .post-it {{
                    padding: 20px 16px 16px;
                    width: 160px;
                    min-height: 140px;
                    box-shadow: 3px 5px 15px rgba(0,0,0,0.2);
                    font-family: 'Caveat', cursive;
                    font-size: 1.1rem;
                    border-radius: 2px 15px 2px 2px;
                    display: flex;
                    flex-direction: column;
                    justify-content: space-between;
                    position: relative;
                    transition: transform 0.3s ease;
                    background-image: linear-gradient(135deg, rgba(255,255,255,0.4) 0%, rgba(255,255,255,0) 100%) !important;
                }}
                .post-it::after {{
                    content: '';
                    position: absolute;
                    top: -6px; left: 50%;
                    transform: translateX(-50%);
                    width: 40px; height: 12px;
                    background: rgba(255,255,255,0.5);
                    box-shadow: 0 1px 2px rgba(0,0,0,0.1);
                }}
                .post-it:hover {{
                    transform: scale(1.1) translateY(-5px) !important;
                    z-index: 10;
                    box-shadow: 5px 15px 25px rgba(0,0,0,0.3);
                }}
                .post-it-msg {{
                    line-height: 1.3;
                    font-weight: 700;
                    color: rgba(0,0,0,0.85);
                }}
                .post-it-autor {{
                    font-size: 0.9rem;
                    font-weight: 700;
                    color: rgba(0,0,0,0.6);
                    text-align: right;
                    margin-top: 15px;
                }}
                .sem-recados {{
                    color: rgba(255,255,255,0.6);
                    font-size: 1.1rem;
                    font-style: italic;
                    padding: 20px 0;
                }}

                /* ── Botão de Impressão ── */
                .btn-imprimir {{
                    position: fixed;
                    bottom: 30px;
                    right: 30px;
                    background-color: #38bdf8;
                    color: #0f172a;
                    border: none;
                    padding: 15px 25px;
                    border-radius: 50px;
                    font-family: 'Lato', sans-serif;
                    font-size: 1.1rem;
                    font-weight: 700;
                    box-shadow: 0 8px 20px rgba(0,0,0,0.4);
                    cursor: pointer;
                    z-index: 1000;
                    transition: all 0.3s ease;
                    display: flex;
                    align-items: center;
                    gap: 10px;
                }}
                .btn-imprimir:hover {{
                    transform: translateY(-5px);
                    background-color: #7dd3fc;
                    box-shadow: 0 12px 25px rgba(0,0,0,0.5);
                }}

                /* ── CONFIGURAÇÕES EXCLUSIVAS PARA A IMPRESSORA (Folha A3 com Cartões Temáticos) ── */
                @media print {{
                    * {{
                        -webkit-print-color-adjust: exact !important;
                        print-color-adjust: exact !important;
                    }}
                    @page {{
                        size: A3 portrait;
                        margin: 1cm;
                    }}
                    /* Remove o fundo de toda a folha para não gastar tinta */
                    body {{
                        background: white !important;
                        color: black !important;
                        padding: 0 !important;
                    }}
                    .btn-imprimir {{
                        display: none !important;
                    }}
                    .mural-header {{
                        background: #f1f5f9 !important;
                        color: #0f172a !important;
                        box-shadow: none !important;
                        border: 2px solid #cbd5e1 !important;
                        margin-bottom: 20px !important;
                        padding: 15px !important;
                    }}
                    .mural-header h1, .mural-header .subtitulo {{
                        color: #0f172a !important;
                        text-shadow: none !important;
                    }}
                    .mural-header .mes-destaque {{
                        -webkit-text-fill-color: #0284c7 !important;
                    }}
                    
                    /* Mágica da Grade de Impressão A3 (2 Colunas) */
                    .mural-grid {{
                        display: grid !important;
                        grid-template-columns: repeat(2, 1fr) !important;
                        grid-auto-rows: 1fr !important;
                        gap: 20px !important;
                        min-height: 85vh !important;
                    }}
                    
                    /* CARTÃO DO ANIVERSARIANTE NA IMPRESSÃO */
                    .aniversariante-row {{
                        /* Aplica a imagem ou cor escolhida no admin SÓ AQUI dentro! */
                        {estilo_fundo_print}
                        
                        /* Película escura (insulfilm) para garantir que o texto branco apareça na impressão */
                        box-shadow: inset 0 0 0 2000px rgba(0, 0, 0, 0.6) !important;
                        
                        border: 2px solid #cbd5e1 !important;
                        border-radius: 20px !important;
                        margin-bottom: 0 !important;
                        
                        /* Layout para a coluna da grade */
                        flex-direction: column !important;
                        align-items: center !important;
                        padding: 20px !important;
                        height: 100% !important;
                        
                        break-inside: avoid !important;
                        page-break-inside: avoid !important;
                    }}
                    
                    /* Força a impressora a puxar uma folha nova a cada 6 pessoas */
                    .aniversariante-row:nth-child(6n) {{
                        page-break-after: always !important;
                        break-after: page !important;
                    }}

                    .polaroid-container {{
                        margin-bottom: 20px !important;
                    }}
                    .recados-section {{
                        width: 100% !important;
                        display: flex !important;
                        flex-direction: column !important;
                        align-items: center !important;
                    }}
                    .recados-titulo {{
                        color: #ffffff !important; /* Mantém branco pois a película do fundo será escura */
                        border-bottom: 2px solid rgba(255,255,255,0.3) !important;
                        width: 100% !important;
                        justify-content: center !important;
                    }}
                    .area-post-it {{
                        justify-content: center !important;
                        width: 100% !important;
                    }}
                    .sem-recados {{
                        color: rgba(255,255,255,0.8) !important;
                    }}
                }}
            </style>
        </head>
        <body>
            <button class="btn-imprimir" onclick="window.print()">🖨️ Extrair para PDF / Imprimir A3</button>

            <div class="mural-header">
                <p class="subtitulo">Celebrações CGC</p>
                <h1>Aniversariantes de <span class="mes-destaque">{nome_mes_atual}</span></h1>
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
                curiosidade_html = f'<div style="font-size:0.85rem; color:#64748b; margin-top:10px; font-style:italic;">"{texto_curiosidade}"</div>'

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
                    <div class="polaroid">
                        {foto_html}
                        <div class="nome">{nome}</div>
                        <div class="data-badge">🎉 {dia} de {nome_mes_atual}</div>
                        {curiosidade_html}
                    </div>
                </div>
                
                <div class="recados-section">
                    <div class="recados-titulo">
                        <span>Mensagens para {nome.split()[0]}</span>
                        <span style="font-size: 1.2rem; opacity: 0.6;">💌</span>
                    </div>
                    <div class="area-post-it">
                        {post_its_html}
                    </div>
                </div>
            </div>
            """

        full_html = html_base + cartoes_html + "</div></body></html>"
        components.html(full_html, height=1800, scrolling=True)

    else:
        st.info(f"🗓️ Nenhum aniversariante cadastrado para {nome_mes_atual}.")
else:
    st.warning("⚠️ Nenhum dado encontrado no banco de dados.")
