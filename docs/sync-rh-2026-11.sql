-- Sincronização do mural com a lista de RH (aniversariantes_rows.xlsx, 24/11/2026)
--
-- Fonte: colunas Nome / Setor / Cargo / Data de Nascimento / Aniversário.
-- As colunas ID, Curiosidade, Foto, Perfil e Senha foram IGNORADAS: estão
-- desalinhadas em relação aos nomes (ex.: Valderlei aparece com ID 19, que é do
-- Gilson). Curiosidades, fotos e senhas do banco ficam preservadas.
--
-- Regras:
--  * Casamento por nome (sem diferenciar maiúsculas/espaços).
--  * Setor e cargo passam a ser os da planilha (cargos em CAIXA ALTA normalizados).
--  * Data: se a planilha traz o ano real, ele é gravado. Sem ano, o banco é
--    mantido; só se o dia/mês do banco estiver vazio ou diferente grava-se
--    1900-MM-DD (convenção de "ano desconhecido").
--  * Ninguém é apagado. O passo 3 apenas LISTA quem está no banco e não está
--    na planilha.
--
-- Idempotente: pode ser reexecutado sem duplicar ninguém.

BEGIN;

DROP TABLE IF EXISTS rh_planilha;
CREATE TEMP TABLE rh_planilha (nome text, setor text, cargo text, dn date, mes int, dia int);
INSERT INTO rh_planilha VALUES
  ('Izaque Ferracini Guimaraes', 'Almoxarifado', 'Assistente de Almoxarifado/Frentista', NULL, 1, 7),
  ('Josimar Carvalho de Souza', 'Almoxarifado', 'Analista de Almoxarifado Pl', NULL, 5, 27),
  ('Marcio Gama de Souza', 'Almoxarifado', 'Assistente de Almoxarifado/Frentista', NULL, 6, 28),
  ('Sergio Francisco da Silva', 'Almoxarifado', 'Auxiliar Administrativo', NULL, 9, 13),
  ('Leandro Bezerra da Costa', 'Almoxarifado', 'Assistente de Almoxarifado/Frentista', NULL, 10, 25),
  ('Osmar Nogueira de Souza Filho', 'Almoxarifado', 'Assistente de Almoxarifado', NULL, 11, 8),
  ('Diego Alberto Pereira Silva', 'Almoxarifado', 'Auxiliar de Almoxarifado/Frentista', '1993-01-20', 1, 20),
  ('Isabela Victoria Xavier de Aguiar', 'Célula de Gestão de Contratos', 'Analista de Gestão de Contratos Jr', NULL, 2, 22),
  ('Déborah Gonçalves', 'Célula de Gestão de Contratos', 'Assistente Administrativo', NULL, 6, 1),
  ('Natallia Pereira Magio', 'Célula de Gestão de Contratos', 'Analista de Gestão de Contratos e Custos Jr', '1994-12-12', 12, 12),
  ('Cleisson dos Santos Bento', 'Controladoria e Contabilidade', 'Especialista Contábil', '1998-02-02', 2, 2),
  ('Thais Mirele da Costa Pincerato Aquino', 'Controladoria e Contabilidade', 'Analista de Planejamento e Análise Financeira Sr', '1985-03-28', 3, 28),
  ('Aline Aquino de Freitas', 'Controladoria e Contabilidade', 'Gerente Administrativo/Financeiro', NULL, 5, 7),
  ('Gesiele da Cruz Pachuri', 'Controladoria e Contabilidade', 'Assistente Administrativo', '1991-06-27', 6, 27),
  ('Daniely Chaves', 'Controladoria e Contabilidade', 'Assistente de Controladoria', NULL, 8, 14),
  ('Daniely Sabriny Jesus Malta', 'Controladoria e Contabilidade', 'Analista Contábil/Fiscal Jr', '1999-10-05', 10, 5),
  ('Thiciane Conceição Rodrigues', 'Controladoria e Contabilidade', 'Auxiliar de Escrituração Fiscal', NULL, 3, 6),
  ('Amanda Valentim Gomes da Mota', 'Performance', 'Assistente Administrativo', NULL, 4, 27),
  ('Fabio De Oliveira Souza', 'Performance', 'Engenheiro de Performance SR', NULL, 12, 27),
  ('Alvaro Guilherme Silva Ramos', 'Performance', 'Estagiário', '2003-02-10', 2, 10),
  ('Jean Jhefferson Siqueira Teixeira', 'Performance', 'Coordenador de Performance', '1990-09-08', 9, 8),
  ('Joao Paulo Santana de Araujo', 'Performance', 'Analista de Performance Sr', '2000-09-25', 9, 25),
  ('Thiago Sobrinho da Conceicao', 'Serviços Gerais', 'Coordenador Administrativo', '1988-05-10', 5, 10),
  ('Antonio Carlos Freitas Pereira', 'Serviços Gerais', 'Motorista de Veículos Leves III', '1973-06-14', 6, 14),
  ('Edson Pereira', 'Serviços Gerais', 'Assistente de Facilites', NULL, 7, 9),
  ('Daiane Souza Vieira', 'Serviços Gerais', 'Analista de Facilites Jr', '1993-07-17', 7, 17),
  ('Gabriel da Silva Mateus', 'Serviços Gerais', 'Auxiliar Administrativo', '2005-08-27', 8, 27),
  ('Ilson Cesar de Mello', 'Serviços Gerais', 'Motorista de Veículos Leves III', '1970-10-05', 10, 5),
  ('Nilson Soares de Souza', 'Serviços Gerais', 'Analista de Facilites Pl', NULL, 11, 4),
  ('Yara Maia Chaves', 'Serviços Gerais', 'Assistente Administrativo', '2004-12-11', 12, 11),
  ('Valderlei Rosa Batista de Jesus', 'Serviços Gerais', 'Técnico Eletricista II', '1974-05-14', 5, 14),
  ('Glaciela Mansano de Sousa', 'Suprimentos', 'Analista de Suprimentos Sr', '1992-04-22', 4, 22),
  ('Gabrielly Reis Lima', 'Suprimentos', 'Jovem Aprendiz', NULL, 6, 16),
  ('Vanclei da Cruz Canteiro', 'Suprimentos', 'Assistente de Compras e Contratos', '1998-08-29', 8, 29),
  ('Gilson Jonas Rodrigues Filho', 'Suprimentos', 'Analista de Compras e Contratos Jr', '1987-09-14', 9, 14),
  ('Iloisio Neves Nascimento', 'Suprimentos', 'Analista de Suprimentos Sr', '1979-10-13', 10, 13),
  ('Amilton Machado de Souza', 'Suprimentos', 'Analista de Compras e Contratos Pl', '1972-11-03', 11, 3),
  ('Jose Neto Candido Rodrigues', 'Suprimentos', 'Analista de Compras e Contratos SR', '1995-08-07', 8, 7),
  ('Fabricio Santana de Lima', 'Tecnologia da Informação', 'Assistente Administrativo', '1990-03-23', 3, 23),
  ('Guilherme Agenor De Almeida', 'Tecnologia da Informação', 'Analista de TI SR', NULL, 12, 28),
  ('Thiago Oliveira Gama', 'Tecnologia da Informação', 'Auxiliar Técnico', '2006-09-07', 9, 7),
  ('Breno Rodrigues Sousa', 'Tecnologia da Informação', 'Tecnologia da Informação', '2007-09-09', 9, 9)
;

-- 1) Atualiza quem já existe
UPDATE public.aniversariantes a
SET setor = v.setor,
    cargo = COALESCE(v.cargo, a.cargo),
    data_nascimento = CASE
        WHEN v.dn IS NOT NULL THEN v.dn
        WHEN v.mes IS NOT NULL AND (a.data_nascimento IS NULL
             OR extract(month FROM a.data_nascimento) <> v.mes
             OR extract(day   FROM a.data_nascimento) <> v.dia)
          THEN make_date(1900, v.mes, v.dia)
        ELSE a.data_nascimento END
FROM rh_planilha v
WHERE upper(btrim(a.nome)) = upper(v.nome);

-- 2) Insere quem ainda não está no banco
INSERT INTO public.aniversariantes (nome, setor, cargo, data_nascimento)
SELECT v.nome, v.setor, v.cargo,
       COALESCE(v.dn, CASE WHEN v.mes IS NOT NULL THEN make_date(1900, v.mes, v.dia) END)
FROM rh_planilha v
WHERE NOT EXISTS (SELECT 1 FROM public.aniversariantes a WHERE upper(btrim(a.nome)) = upper(v.nome));

COMMIT;

-- 3) Quem está no banco mas NÃO está na planilha (só consulta — nada é apagado)
SELECT a.id, a.nome, a.setor, a.cargo
FROM public.aniversariantes a
WHERE NOT EXISTS (SELECT 1 FROM rh_planilha v WHERE upper(btrim(a.nome)) = upper(v.nome))
ORDER BY a.nome;
