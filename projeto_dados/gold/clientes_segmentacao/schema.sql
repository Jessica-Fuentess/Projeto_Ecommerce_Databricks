CREATE MATERIALIZED VIEW `projeto_dados`.`gold`.`clientes_segmentacao` (
  id_cliente STRING COLLATE UTF8_BINARY COMMENT 'Identificador do cliente (prefixo cus_).',
  nome_cliente STRING COLLATE UTF8_BINARY COMMENT 'Nome do cliente, sem pronome de tratamento.',
  estado STRING COLLATE UTF8_BINARY COMMENT 'Sigla da UF do cliente, por exemplo SP, RJ, MG.',
  nome_estado STRING COLLATE UTF8_BINARY COMMENT 'Nome completo do estado (fonte: API do IBGE).',
  regiao STRING COLLATE UTF8_BINARY COMMENT 'Região do Brasil: Norte, Nordeste, Centro-Oeste, Sudeste ou Sul (fonte: API do IBGE).',
  total_compras BIGINT COMMENT 'Quantidade de compras do cliente no período.',
  receita DECIMAL(20,2) COMMENT 'Receita total gerada pelo cliente no período, em reais (R$).',
  ticket_medio DECIMAL(11,2) COMMENT 'Valor médio por compra do cliente, em reais (R$).',
  primeira_compra DATE COMMENT 'Data da primeira compra do cliente.',
  ultima_compra DATE COMMENT 'Data da compra mais recente do cliente.',
  segmento_cliente STRING COLLATE UTF8_BINARY COMMENT 'Segmento pela receita no período: VIP (a partir de R$ 22.000), TOP_TIER (R$ 17.000 a R$ 21.999,99) ou REGULAR (abaixo de R$ 17.000).',
  ranking_receita INT COMMENT 'Posição do cliente no ranking de receita (1 = cliente que mais gerou receita).')
COMMENT 'Uma linha por cliente com receita, compras, ticket médio, região e segmento. Use para perguntas sobre melhores clientes, clientes VIP, segmentos, estados e regiões.'
AS WITH receita_por_cliente AS (
  SELECT
    c.id_cliente,
    c.nome_cliente,
    c.estado,
    c.nome_estado,
    c.regiao,
    COUNT(v.id_venda)           AS total_compras,
    COALESCE(SUM(v.receita), 0) AS receita,
    ROUND(AVG(v.receita), 2)    AS ticket_medio,
    MIN(v.data)                 AS primeira_compra,
    MAX(v.data)                 AS ultima_compra
  FROM silver.clientes c
  LEFT JOIN silver.vendas v
    ON c.id_cliente = v.id_cliente
  GROUP BY ALL
)
SELECT
  *,
  CASE
    WHEN receita >= 22000 THEN 'VIP'
    WHEN receita >= 17000 THEN 'TOP_TIER'
    ELSE 'REGULAR'
  END                                       AS segmento_cliente,
  ROW_NUMBER() OVER (ORDER BY receita DESC) AS ranking_receita
FROM receita_por_cliente
