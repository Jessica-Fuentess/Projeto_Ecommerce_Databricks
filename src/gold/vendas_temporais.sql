-- Gold · vendas no tempo (diretoria Comercial)
-- Grão: uma linha por dia × hora × canal.
--
-- Responde "quanto vendemos por dia, por hora, por canal?". Inclui TODAS as vendas, inclusive
-- as de produtos não cadastrados: dinheiro que entrou é receita.
--
-- Os comentários das colunas documentam a semântica dos indicadores
-- para consumo analítico e por ferramentas de linguagem natural.

CREATE OR REFRESH MATERIALIZED VIEW gold.vendas_temporais (
  data            DATE          COMMENT 'Data da venda (sem horário).',
  dia_semana      STRING        COMMENT 'Dia da semana em português: Domingo, Segunda, Terça, Quarta, Quinta, Sexta, Sábado.',
  dia_semana_num  INT           COMMENT 'Número do dia da semana para ordenação: 1 = Domingo ... 7 = Sábado.',
  hora            INT           COMMENT 'Hora do dia da venda, de 0 a 23.',
  canal_venda     STRING        COMMENT 'Canal da venda: ecommerce (site) ou loja_fisica.',
  total_vendas    BIGINT        COMMENT 'Quantidade de vendas (pedidos). Somar para totalizar.',
  itens_vendidos  BIGINT        COMMENT 'Quantidade de unidades vendidas. Somar para totalizar.',
  receita         DECIMAL(20,2) COMMENT 'Receita bruta em reais (R$) = quantidade × preço unitário. Somar para totalizar.',
  clientes_unicos BIGINT        COMMENT 'Clientes distintos NAQUELA linha (dia, hora, canal). Não somar entre linhas: para clientes únicos no período use gold.clientes_segmentacao.'
)
COMMENT 'Vendas agregadas por dia, hora e canal.'
AS
SELECT
  data,
  dia_semana,
  dia_semana_num,
  hora,
  canal_venda,
  COUNT(*)                   AS total_vendas,
  SUM(quantidade)            AS itens_vendidos,
  SUM(receita)               AS receita,
  COUNT(DISTINCT id_cliente) AS clientes_unicos
FROM silver.vendas
GROUP BY data, dia_semana, dia_semana_num, hora, canal_venda;
