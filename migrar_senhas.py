"""
migrar_senhas.py
────────────────
Roda UMA ÚNICA VEZ para hashear (bcrypt) as senhas que ainda estão em texto puro.

Como cada valor é tratado:
  - Hash bcrypt ($2a$/$2b$/$2y$) → já protegido, ignorado.
  - Hash SHA-256 (64 chars hex)  → legado já hasheado; IGNORADO.
    NUNCA re-hashear, pois bcrypt(sha256) destruiria a senha de forma
    irreversível (o login deixaria de funcionar). O app já verifica
    SHA-256 nativamente e re-grava em bcrypt na próxima edição de perfil.
  - Qualquer outro valor → texto puro, migrado para bcrypt.

Uso:
    pip install bcrypt
    python migrar_senhas.py
"""

import re
import bcrypt
from utils import get_supabase   # mesmo utilitário já usado no app

def is_bcrypt(valor: str) -> bool:
    """Retorna True se o valor já é um hash bcrypt."""
    return isinstance(valor, str) and valor.startswith(("$2a$", "$2b$", "$2y$"))

def is_sha256(valor: str) -> bool:
    """
    Retorna True se o valor parece um hash SHA-256 (64 chars hexadecimais).
    Importante: NÃO se pode re-hashear um SHA-256 como se fosse texto puro,
    pois isso destruiria a senha original de forma irreversível.
    """
    return isinstance(valor, str) and bool(re.fullmatch(r"[0-9a-fA-F]{64}", valor))

def migrar():
    supabase = get_supabase()

    print("🔍 Buscando aniversariantes...")
    resp = supabase.table("aniversariantes").select("id, nome, senha_perfil").execute()
    registros = resp.data or []

    total      = len(registros)
    migrados   = 0
    ignorados  = 0  # já tinham hash bcrypt
    sha_legado = 0  # SHA-256 — deixados como estão
    sem_senha  = 0  # NULL ou vazio

    for reg in registros:
        rid        = reg["id"]
        nome       = reg.get("nome", "?")
        senha_raw  = reg.get("senha_perfil")

        # Pula registros sem senha
        if not senha_raw:
            print(f"  ⚪ [{rid}] {nome} — sem senha, ignorado")
            sem_senha += 1
            continue

        # Pula quem já tem hash bcrypt
        if is_bcrypt(senha_raw):
            print(f"  ✅ [{rid}] {nome} — já possui hash bcrypt, ignorado")
            ignorados += 1
            continue

        # Pula hashes SHA-256 (re-hashear corromperia a senha)
        if is_sha256(senha_raw):
            print(f"  🟡 [{rid}] {nome} — hash SHA-256 legado, preservado")
            sha_legado += 1
            continue

        # Hasheia a senha em texto puro
        novo_hash = bcrypt.hashpw(
            senha_raw.encode("utf-8"),
            bcrypt.gensalt()
        ).decode("utf-8")

        supabase.table("aniversariantes").update(
            {"senha_perfil": novo_hash}
        ).eq("id", rid).execute()

        print(f"  🔒 [{rid}] {nome} — senha migrada para bcrypt")
        migrados += 1

    print("\n" + "─" * 50)
    print(f"✔ Concluído! Total: {total} | Migrados: {migrados} | "
          f"Já bcrypt: {ignorados} | SHA-256 legado: {sha_legado} | "
          f"Sem senha: {sem_senha}")

if __name__ == "__main__":
    migrar()
