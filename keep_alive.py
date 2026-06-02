from utils import get_supabase

try:
    # Usa a sua própria função de conexão já configurada
    supabase = get_supabase()
    
    # Faz um select simples puxando apenas 1 ID para não gastar banda
    supabase.table("aniversariantes").select("id").limit(1).execute()
    
    print("Ping no Supabase realizado com sucesso! O projeto não vai pausar.")
except Exception as e:
    print(f"Erro ao pingar o Supabase: {e}")
