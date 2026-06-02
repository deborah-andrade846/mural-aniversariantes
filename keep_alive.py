import os
from supabase import create_client

# 1. Pega as credenciais diretamente das variáveis de ambiente do GitHub Actions
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")

# 2. Trava de segurança caso as credenciais não estejam no GitHub
if not url or not key:
    print("Erro: SUPABASE_URL ou SUPABASE_KEY não foram encontrados no GitHub Secrets.")
    exit(1)

# 3. Faz a conexão direta sem usar o Streamlit
try:
    supabase = create_client(url, key)
    
    # Faz a consulta leve para simular uso no banco
    supabase.table("aniversariantes").select("id").limit(1).execute()
    
    print("Ping no Supabase realizado com sucesso! O projeto não vai pausar. 🎉")
except Exception as e:
    print(f"Erro ao pingar o Supabase: {e}")
