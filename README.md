# 🎉 Mural de Aniversariantes — GAFI

Aplicação em [Streamlit](https://streamlit.io/) para exibir um mural interativo
de aniversariantes, com fotos, recados em post-its, pesquisa de satisfação e
modo TV para exibição em telão.

## ✨ Funcionalidades

- **Mural principal** (`app.py`): cartões dos aniversariantes do mês, recados em
  post-its e destaque para quem faz aniversário no dia.
- **Cadastro** (`pages/1_Cadastro.py`): colaboradores completam o perfil (foto,
  curiosidade) protegido por senha.
- **Recados** (`pages/2_Recados.py`): mensagens públicas para os aniversariantes.
- **Colaboradores** (`pages/3_Colaboradores.py`): lista completa por mês.
- **Pesquisa de satisfação** (`pages/4_📊_Pesquisa.py`): formulário e painel de
  resultados (admin).
- **Modo TV**: acesse com `?tv=true` para exibição em telão (auto-refresh).

## 🚀 Como rodar localmente

```bash
pip install -r requirements.txt
streamlit run app.py
```

### Segredos necessários (`.streamlit/secrets.toml`)

```toml
SUPABASE_URL   = "https://xxxx.supabase.co"
SUPABASE_KEY   = "chave-anon-ou-service"
ADMIN_PASSWORD = "senha-do-painel-admin"
```

## 🔐 Senhas de perfil

As senhas dos perfis são protegidas com **bcrypt** (`utils.hash_senha`).
A verificação (`utils.verificar_senha`) também aceita, por compatibilidade,
hashes SHA-256 e texto puro antigos — esses são re-gravados em bcrypt na
próxima edição do perfil.

O script `migrar_senhas.py` converte para bcrypt apenas senhas que ainda
estejam em texto puro; hashes bcrypt e SHA-256 já existentes são preservados
(nunca re-hasheados, o que destruiria a senha).

## 🗄️ Banco de dados (Supabase)

Tabelas usadas:

- `aniversariantes` — `id`, `nome`, `data_nascimento`, `curiosidade`,
  `foto_url`, `senha_perfil`, `perfil_completo`
- `recados` — `para_quem`, `de_quem`, `mensagem`
- `pesquisa_satisfacao` — notas e sugestões por categoria
- `configuracoes_mural` — pares `chave`/`valor` (flags e personalização)

O workflow `.github/workflows/keep_alive.yml` faz um ping periódico para evitar
que o projeto Supabase entre em pausa por inatividade.

## 📁 Estrutura

```
app.py                 # mural principal
utils.py               # conexão Supabase, hashing, helpers
keep_alive.py          # ping anti-pausa do Supabase
migrar_senhas.py       # migração pontual de senhas para bcrypt
pages/                 # páginas adicionais do Streamlit
requirements.txt       # dependências
```
