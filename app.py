import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
from datetime import datetime
from supabase import create_client, Client
import random # Usado para entortar os post-its aleatoriamente

st.set_page_config(page_title="Mural de Clima", layout="wide", page_icon="🎉")

# -- PERSONALIZAÇÃO DE COR --
st.sidebar.title("🎨 Personalizar Mural")
# Cor padrão é o azul escuro executivo. Você pode mudar pelo menu lateral!
cor_fundo = st.sidebar.color_picker("Escolha a cor de fundo", "#0f172a")

# Conexão com Supabase
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

mes_atual = datetime.now().month
meses_ptbr = {1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril', 5: 'Maio', 6: 'Junho', 
              7: 'Julho', 8: 'Agosto', 9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'}
nome_mes_atual = meses_ptbr[mes_atual]

try:
    response = supabase.table("aniversariantes").select("*").execute()
    dados = response.data
    
    # Busca os recados no banco
    resp_recados = supabase.table("recados").select("*").execute()
    df_recados = pd.DataFrame(resp_recados.data)
except Exception as e:
    st.error(f"Erro ao conectar com o banco: {e}")
    dados = []

if dados:
    df = pd.DataFrame(dados)
    df['data_nascimento'] = pd.to_datetime(df['data_nascimento'])
    df_mes = df[df['data_nascimento'].dt.month == mes_atual].copy()
    
    if not df_mes.empty:
        df_mes = df_mes.sort_values(by='data_nascimento')
        
        # Repare que o CSS agora usa a variável {cor_fundo}
        html_base = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                * {{ margin: 0; padding: 0; box-sizing: border-box; font-family: 'Segoe UI', sans-serif; }}
                body {{ background-color: {cor_fundo}; color: #f8fafc; display: flex; flex-direction: column; align-items: center; padding: 30px 20px; transition: background-color 0.5s ease; }}
                .mural-header {{ text-align: center; margin-bottom: 50px; }}
                .mural-header h1 {{ font-size: 3rem; text-transform: uppercase; letter-spacing: 3px; color: #f8fafc; border-bottom: 2px solid #38bdf8; padding-bottom: 10px; display: inline-block; }}
                .mural-grid {{ display: flex; flex-wrap: wrap; gap: 40px; justify-content: center; max-width: 1200px; }}
                .aniversariante-card {{ display: flex; flex-direction: column; align-items: center; gap: 20px; }}
                .polaroid {{ background-color: #ffffff; padding: 15px 15px 30px 15px; border-radius: 4px; box-shadow: 0 10px 25px rgba(0,0,0,0.5); width: 250px; color: #1e293b; text-align: center; z-index: 2; }}
                .polaroid:nth-child(even) {{ transform: rotate(2deg); }}
                .polaroid:nth-child(odd) {{ transform: rotate(-2deg); }}
                .foto {{ width: 100%; height: 220px; background-color: #e2e8f0; background-size: cover; background-position: center; margin-bottom: 15px; border: 1px solid #cbd5e1; border-radius: 2px; }}
                .nome {{ font-size: 1.5rem; font-weight: bold; margin-bottom: 5px; }}
                .data {{ font-size: 1rem; color: #ef4444; font-weight: bold; margin-bottom: 10px; }}
                
                /* Área de post-its adaptada para receber vários itens */
                .area-post-it {{ border: 2px dashed rgba(255,255,255,0.3); border-radius: 8px; width: 300px; min-height: 200px; padding: 10px; display: flex; flex-wrap: wrap; gap: 10px; justify-content: center; align-items: flex-start; }}
                
                /* Estilo do Post-it Digital */
                .post-it {{ background-color: #fef08a; color: #3f6212; padding: 15px; width: 130px; box-shadow: 2px 4px 6px rgba(0,0,0,0.3); font-family: 'Comic Sans MS', cursive, sans-serif; font-size: 0.85rem; border-radius: 2px; }}
            </style>
        </head>
        <body>
            <div class="mural-header">
                <h1>Aniversariantes de {nome_mes_atual}</h1>
            </div>
            <div class="mural-grid">
        """

        cartoes_html = ""
        for index, row in df_mes.iterrows():
            dia_aniversario = row['data_nascimento'].day
            
            imagem_bg = "linear-gradient(45deg, #e2e8f0 25%, #cbd5e1 25%, #cbd5e1 50%, #e2e8f0 50%, #e2e8f0 75%, #cbd5e1 75%, #cbd5e1 100%)"
            if pd.notna(row['foto_url']) and str(row['foto_url']).strip() != "":
                imagem_bg = f"url('{row['foto_url']}')"
                
            curiosidade = row['curiosidade'] if pd.notna(row['curiosidade']) and str(row['curiosidade']).strip() != "" else ""

            # --- LÓGICA DE GERAR OS POST-ITS DESSA PESSOA ---
            post_its_html = ""
            if not df_recados.empty:
                # Filtra os recados apenas para o nome desta pessoa
                recados_pessoa = df_recados[df_recados['para_quem'] == row['nome']]
                
                if recados_pessoa.empty:
                    post_its_html = "<p style='color: rgba(255,255,255,0.5); font-size: 0.9rem; margin-top: 80px;'>Deixe um recado na aba lateral 📌</p>"
                else:
                    for i, recado in recados_pessoa.iterrows():
                        # Cria uma rotação aleatória para cada post-it não ficar reto parecendo robótico
                        rotacao = random.randint(-6, 6)
                        post_its_html += f"""
                        <div class="post-it" style="transform: rotate({rotacao}deg);">
                            <strong>"{recado['mensagem']}"</strong><br><br>
                            <small>✏️ {recado['de_quem']}</small>
                        </div>
                        """
            else:
                post_its_html = "<p style='color: rgba(255,255,255,0.5); font-size: 0.9rem; margin-top: 80px;'>Deixe um recado na aba lateral 📌</p>"

            # Montagem final do cartão com a área de post-its preenchida
            cartao = f"""
                <div class="aniversariante-card">
                    <div class="polaroid">
                        <div class="foto" style="background-image: {imagem_bg};"></div>
                        <div class="nome">{row['nome']}</div>
                        <div class="data">{dia_aniversario} de {nome_mes_atual}</div>
                        <div class="curiosidade" style="font-size: 0.85rem; color: #64748b;"><i>{curiosidade}</i></div>
                    </div>
                    <div class="area-post-it">
                        {post_its_html}
                    </div>
                </div>
            """
            cartoes_html += cartao

        html_fim = """
            </div>
        </body>
        </html>
        """
        
        html_completo = html_base + cartoes_html + html_fim
        components.html(html_completo, height=1200, scrolling=True)
