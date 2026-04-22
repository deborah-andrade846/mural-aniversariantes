import streamlit as st
from supabase import create_client, Client
import hashlib
import re


@st.cache_resource
def get_supabase() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)


def hash_senha(senha: str) -> str:
    """Retorna o SHA-256 da senha em hex."""
    return hashlib.sha256(senha.strip().encode()).hexdigest()


def verificar_senha(senha_digitada: str, hash_no_banco: str) -> bool:
    """Compara a senha digitada (em texto puro ou já em hash) com o banco."""
    if not senha_digitada or not hash_no_banco:
        return False
    # Suporte a senhas antigas (texto puro) e novas (hash)
    if len(hash_no_banco) == 64:  # SHA-256 hex tem 64 chars
        return hash_senha(senha_digitada) == hash_no_banco
    return senha_digitada == hash_no_banco  # legado


def to_bool(val, default=False) -> bool:
    if isinstance(val, bool):
        return val
    if isinstance(val, str):
        return val.strip().lower() in ('true', '1', 'yes', 'sim')
    return default


def cor_hex_valida(valor) -> bool:
    return isinstance(valor, str) and bool(re.fullmatch(r"#[0-9a-fA-F]{6}", valor.strip()))


def carregar_config() -> dict:
    try:
        supabase = get_supabase()
        resp = supabase.table("configuracoes_mural").select("*").execute()
        return {item['chave']: item['valor'] for item in resp.data}
    except Exception:
        return {}


def cor_texto_contraste(hex_bg: str) -> str:
    """
    Analisa uma cor hexadecimal de fundo e retorna #000000 (preto) 
    ou #FFFFFF (branco) para garantir a melhor leitura do texto.
    """
    hex_bg = hex_bg.lstrip('#')
    if len(hex_bg) != 6:
        return "#000000"
        
    r, g, b = tuple(int(hex_bg[i:i+2], 16) for i in (0, 2, 4))
    luminosidade = (0.299 * r + 0.587 * g + 0.114 * b)
    
    if luminosidade > 128:
        return "#000000"
    else:
        return "#FFFFFF"
