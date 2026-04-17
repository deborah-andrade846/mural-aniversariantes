import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
from datetime import datetime
from supabase import create_client, Client

st.set_page_config(page_title="Mural de Clima", layout="wide", page_icon="🎉")

# Conexão com Supabase
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

# Identificar o mês atual
mes_atual = datetime.now().month
meses_ptbr = {1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril', 5: 'Maio', 6: 'Junho', 
              7: 'Julho', 8: 'Agosto', 9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'}
nome_mes_atual = meses_ptbr[mes_atual]

# Buscar dados da nuvem
try:
    response = supabase.table("aniversariantes").select("*").execute()
    dados = response.data
except Exception as e:
    st.error(f"Erro ao conectar com o banco: {e}")
    dados = []

if not dados:
    st.info("Nenhum colaborador cadastrado ainda. Use o menu lateral para acessar o Formulário!")
else:
    # Transformar em DataFrame e filtrar pelo mês atual
    df = pd.DataFrame(dados)
    df['data_nascimento'] = pd.to_datetime(df['data_nascimento'])
    df_mes = df[df['data_nascimento'].dt.month == mes_atual].copy()
    
    if df_mes.empty:
        st.warning(f"Nenhum aniversariante encontrado para o mês de {nome_mes_atual}.")
    else:
        # Ordenar por dia
        df_mes = df_mes.sort_values(by='data_nascimento')
        
        # --- ESTRUTURA HTML ---
        html_base = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                * {{ margin: 0; padding: 0; box-sizing: border-box; font-family: 'Segoe UI', sans-serif; }}
                body {{ background-color: #0f172a; color: #f8fafc; display: flex; flex-direction: column; align-items: center; padding: 30px 20px; }}
                .mural-header {{ text-align: center; margin-bottom: 50px; }}
                .mural-header h1 {{ font-size: 3rem; text-transform: uppercase; letter-spacing: 3px; color: #38bdf8; border-bottom: 2px solid #38bdf8; padding-bottom: 10px; display: inline-block; }}
                .mural-header p {{ margin-top: 10px; font-size: 1.2rem; color: #94a3b8; }}
                .mural-grid {{ display: flex; flex-wrap: wrap; gap: 40px; justify-content: center; max-width: 1200px; }}
                .aniversariante-card {{ display: flex; flex-direction: column; align-items: center; gap: 20px; }}
                .polaroid {{ background-color: #ffffff; padding: 15px 15px 30px 15px; border-radius: 4px; box-shadow: 0 10px 25px rgba(0,0,0,0.5); width: 250px; color: #1e293b; text-align: center; }}
                .polaroid:nth-child(even) {{ transform: rotate(2deg); }}
                .polaroid:nth-child(odd) {{ transform: rotate(-2deg); }}
                .foto {{ width: 100%; height: 220px; background-color: #e2e8f0; background-size: cover; background-position: center; margin-bottom: 15px; border: 1px solid #cbd5e1; border-radius: 2px; }}
                .nome {{ font-size: 1.5rem; font-weight: bold; margin-bottom: 5px; }}
                .data {{ font-size: 1rem; color: #ef4444; font-weight: bold; margin-bottom: 10px; }}
                .curiosidade {{ font-size: 0.9rem; font-style: italic; color: #64748b; line-height: 1.4; }}
                .area-post-it {{ border: 2px dashed #475569; border-radius: 8px; width: 280px; min-height: 200px; display: flex; align-items: center; justify-content: center; }}
                .area-post-it::before {{ content: "Espaço para recados 📌"; color: #475569; font-size: 1rem; opacity: 0.5; }}
            </style>
        </head>
        <body>
            <div class="mural-header">
                <h1>Aniversariantes de {nome_mes_atual}</h1>
                <p>Deixe seu recado e participe do nosso café de integração!</p>
            </div>
            <div class="mural-grid">
        """

        cartoes_html = ""
        for index, row in df_mes.iterrows():
            dia_aniversario = row['data_nascimento'].day
            
            # Checagem se a foto está vazia
            if pd.isna(row['foto_url']) or str(row['foto_url']).strip() == "":
                imagem_bg = "linear-gradient(45deg, #e2e8f0 25%, #cbd5e1 25%, #cbd5e1 50%, #e2e8f0 50%, #e2e8f0 75%, #cbd5e1 75%, #cbd5e1 100%)"
            else:
                imagem_bg = f"url('{row['foto_url']}')"
                
            curiosidade = row['curiosidade'] if pd.notna(row['curiosidade']) and str(row['curiosidade']).strip() != "" else "Escreva um recado para mim!"

            cartao = f"""
                <div class="aniversariante-card">
                    <div class="polaroid">
                        <div class="foto" style="background-image: {imagem_bg};"></div>
                        <div class="nome">{row['nome']}</div>
                        <div class="data">{dia_aniversario} de {nome_mes_atual}</div>
                        <div class="curiosidade">"{curiosidade}"</div>
                    </div>
                    <div class="area-post-it"></div>
                </div>
            """
            cartoes_html += cartao

        html_fim = """
            </div>
        </body>
        </html>
        """
        
        # Renderiza o HTML criado direto dentro do Streamlit
        html_completo = html_base + cartoes_html + html_fim
        components.html(html_completo, height=900, scrolling=True)