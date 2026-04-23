"""
migrar_senhas.py
────────────────
Roda UMA ÚNICA VEZ para hashear as senhas antigas que ainda estão em texto puro.

Como identificar senha em texto puro:
  - Hashes bcrypt sempre começam com "$2b$" ou "$2a$"
  - Qualquer outro valor é texto puro e precisa ser migrado

Uso:
    pip install bcrypt
    python migrar_senhas.py

O script imprime um resumo do que foi feito e não altera registros
que já possuem hash bcrypt.
"""

import bcrypt
from utils import get_supabase   # mesmo utilitário já usado no app

def is_bcrypt(valor: str) -> bool:
    """Retorna True se o valor já é um hash bcrypt."""
    return isinstance(valor, str) and (
        valor.startswith("$2b$") or valor.startswith("$2a$")
    )

def migrar():
    supabase = get_supabase()

    print("🔍 Buscando aniversariantes...")
    resp = supabase.table("aniversariantes").select("id, nome, senha_perfil").execute()
    registros = resp.data or []

    total      = len(registros)
    migrados   = 0
    ignorados  = 0  # já tinham hash
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
            print(f"  ✅ [{rid}] {nome} — já possui hash, ignorado")
            ignorados += 1
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
          f"Já hashados: {ignorados} | Sem senha: {sem_senha}")

if __name__ == "__main__":
    migrar()
