import streamlit as st
from supabase import create_client, Client
import hashlib
import re
import bcrypt


@st.cache_resource
def get_supabase() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)


def _is_bcrypt(valor: str) -> bool:
    """True se o valor já é um hash bcrypt ($2a$/$2b$/$2y$)."""
    return isinstance(valor, str) and valor.startswith(("$2a$", "$2b$", "$2y$"))


def _is_sha256(valor: str) -> bool:
    """True se o valor parece um hash SHA-256 (64 chars hexadecimais)."""
    return isinstance(valor, str) and bool(re.fullmatch(r"[0-9a-fA-F]{64}", valor))


def hash_senha(senha: str) -> str:
    """
    Gera um hash bcrypt (com salt) da senha. Esquema padrão do projeto.
    bcrypt limita a 72 bytes; senhas maiores são truncadas pela própria lib.
    """
    senha_bytes = senha.strip().encode("utf-8")
    return bcrypt.hashpw(senha_bytes, bcrypt.gensalt()).decode("utf-8")


def verificar_senha(senha_digitada: str, hash_no_banco: str) -> bool:
    """
    Verifica a senha contra o valor guardado no banco, com suporte a três
    formatos para retro-compatibilidade durante a transição:
      1. bcrypt   (novo padrão)
      2. SHA-256  (legado — hex de 64 chars)
      3. texto puro (legado antigo)
    """
    if not senha_digitada or not hash_no_banco:
        return False

    if _is_bcrypt(hash_no_banco):
        try:
            return bcrypt.checkpw(
                senha_digitada.strip().encode("utf-8"),
                hash_no_banco.encode("utf-8"),
            )
        except (ValueError, TypeError):
            return False

    if _is_sha256(hash_no_banco):
        sha = hashlib.sha256(senha_digitada.strip().encode()).hexdigest()
        return sha == hash_no_banco

    return senha_digitada == hash_no_banco  # legado antigo (texto puro)


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
