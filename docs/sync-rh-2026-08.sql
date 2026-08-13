-- Sincronização do mural com a lista de RH (aniversariantes_rows.xlsx, 12/08/2026)
--
-- Fonte: colunas Nome / Setor / Cargo / Data de Nascimento da planilha.
-- As colunas ID, Curiosidade, Foto, Perfil e Senha da planilha estão DESLOCADAS
-- a partir da linha 20 (a curiosidade da Amanda aparece no Joselito, etc.) e por
-- isso foram ignoradas — esses dados já estão corretos no banco.
--
-- Idempotente: pode ser reexecutado sem duplicar ninguém.

BEGIN;

-- 1) Padronização de grafia dos nomes + anos de nascimento reais
--    (o banco usava 1900 como marcador de "ano desconhecido")
UPDATE public.aniversariantes SET nome = 'Izaque Ferracini Guimaraes' WHERE id = 22;
UPDATE public.aniversariantes SET nome = 'Josimar Carvalho de Souza' WHERE id = 27;
UPDATE public.aniversariantes SET nome = 'Marcio Gama de Souza' WHERE id = 30;
UPDATE public.aniversariantes SET nome = 'Sergio Francisco da Silva' WHERE id = 40;
UPDATE public.aniversariantes SET nome = 'Leandro Bezerra da Costa' WHERE id = 42;
UPDATE public.aniversariantes SET nome = 'Osmar Nogueira de Souza Filho' WHERE id = 46;
UPDATE public.aniversariantes SET nome = 'Isabela Victoria Xavier de Aguiar' WHERE id = 24;
UPDATE public.aniversariantes SET nome = 'Thais Mirele da Costa Pincerato Aquino' WHERE id = 25;
UPDATE public.aniversariantes SET nome = 'Aline Aquino de Freitas' WHERE id = 29;
UPDATE public.aniversariantes SET nome = 'Daniely Chaves' WHERE id = 39;
UPDATE public.aniversariantes SET nome = 'Daniely Sabriny Jesus Malta' WHERE id = 45;
UPDATE public.aniversariantes SET nome = 'Amanda Valentim Gomes da Mota' WHERE id = 52;
UPDATE public.aniversariantes SET nome = 'Thiago Sobrinho da Conceicao' WHERE id = 28;
UPDATE public.aniversariantes SET nome = 'Lethicia Oliveira Leopoldo' WHERE id = 31;
UPDATE public.aniversariantes SET nome = 'Antonio Carlos Freitas Pereira', data_nascimento = '1973-06-14' WHERE id = 32;
UPDATE public.aniversariantes SET nome = 'Edson Pereira' WHERE id = 34;
UPDATE public.aniversariantes SET nome = 'Gabriel da Silva Mateus', data_nascimento = '2005-08-27' WHERE id = 37;
UPDATE public.aniversariantes SET nome = 'Ilson Cesar de Mello', data_nascimento = '1970-10-05' WHERE id = 43;
UPDATE public.aniversariantes SET nome = 'Nilson Soares de Souza' WHERE id = 47;
UPDATE public.aniversariantes SET nome = 'Yara Maia Chaves', data_nascimento = '2004-12-11' WHERE id = 50;
UPDATE public.aniversariantes SET nome = 'Vanclei da Cruz Canteiro' WHERE id = 38;
UPDATE public.aniversariantes SET nome = 'Gilson Jonas Rodrigues Filho' WHERE id = 19;
UPDATE public.aniversariantes SET nome = 'Iloisio Neves Nascimento' WHERE id = 44;
UPDATE public.aniversariantes SET nome = 'Francielle de Fatima Fernandes' WHERE id = 49;

-- 2) Novos colaboradores (12)
INSERT INTO public.aniversariantes (nome, data_nascimento, setor, cargo)
SELECT v.nome, v.data_nascimento::date, v.setor, v.cargo
FROM (VALUES

  ('Diego Alberto Pereira Silva', '1993-01-20', 'Almoxarifado', 'Auxiliar de Almoxarifado/Frentista'),
  ('Thalita Bregantin Silva Casto', '2000-06-08', 'Controladoria e Contabilidade', 'Assistente de Escrituração Fiscal'),
  ('Thiciane Conceição Rodrigues', '1900-03-06', 'Controladoria e Contabilidade', 'Auxiliar de Escrituração Fiscal'),
  ('Joselito Teles dos Santos', '1900-04-10', 'Controladoria e Contabilidade', 'Analista Tributário SR'),
  ('Marcos Vinicios Nascimento Aleixo', '1900-10-22', 'Performance', 'Analista de PCP PL'),
  ('Fabio De Oliveira Souza', '1900-12-27', 'Performance', 'Engenheiro de Performance SR'),
  ('Alvaro Guilherme Silva Ramos', '2003-02-10', 'Performance', 'Estagiário'),
  ('Andressa Baldin Dos Santos Oliveira', '1900-01-29', 'Serviços Gerais', 'Jovem Aprendiz'),
  ('Valderlei Rosa Batista de Jesus', '1974-05-14', 'Serviços Gerais', 'Técnico Eletricista II'),
  ('Guilherme Agenor De Almeida', NULL, 'Tecnologia da Informação', 'Analista de TI SR'),
  ('Thiago Oliveira Gama', '2006-09-07', 'Tecnologia da Informação', NULL),
  ('Breno Rodrigues Sousa', '2007-09-09', 'Tecnologia da Informação', 'Tecnologia da Informação')
) AS v(nome, data_nascimento, setor, cargo)
WHERE NOT EXISTS (
    SELECT 1 FROM public.aniversariantes a
    WHERE upper(a.nome) = upper(v.nome)
);

COMMIT;
