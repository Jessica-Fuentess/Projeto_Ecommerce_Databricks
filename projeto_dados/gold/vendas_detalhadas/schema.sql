CREATE MATERIALIZED VIEW `projeto_dados`.`gold`.`vendas_detalhadas` (
  id_venda STRING COLLATE UTF8_BINARY COMMENT 'Identificador da venda (prefixo sal_). Uma linha por venda.',
  data_venda TIMESTAMP COMMENT 'Data e hora da venda.',
  data DATE COMMENT 'Data da venda (sem horário).',
  dia_semana STRING COLLATE UTF8_BINARY COMMENT 'Dia da semana em português: Domingo, Segunda, Terça, Quarta, Quinta, Sexta, Sábado.',
  dia_semana_num INT COMMENT 'Número do dia da semana para ordenação: 1 = Domingo ... 7 = Sábado.',
  hora INT COMMENT 'Hora do dia da venda, de 0 a 23.',
  canal_venda STRING COLLATE UTF8_BINARY COMMENT 'Canal da venda: ecommerce (site) ou loja_fisica.',
  id_produto STRING COLLATE UTF8_BINARY COMMENT 'Identificador do produto (prefixo prd_).',
  nome_produto STRING COLLATE UTF8_BINARY COMMENT 'Nome do produto, ou "Produto não cadastrado". Produtos diferentes podem ter o mesmo nome; use id_produto para contar produtos.',
  categoria STRING COLLATE UTF8_BINARY COMMENT 'Categoria do produto, ou "Não cadastrado".',
  marca STRING COLLATE UTF8_BINARY COMMENT 'Marca do produto, ou "Não cadastrado".',
  faixa_preco STRING COLLATE UTF8_BINARY COMMENT 'Faixa de preço do produto: PREMIUM, MEDIO ou BASICO. Vazia para produto não cadastrado.',
  produto_cadastrado BOOLEAN COMMENT 'false quando o produto vendido não existe no catálogo (problema de qualidade de dados).',
  id_cliente STRING COLLATE UTF8_BINARY COMMENT 'Identificador do cliente (prefixo cus_).',
  nome_cliente STRING COLLATE UTF8_BINARY COMMENT 'Nome do cliente, sem pronome de tratamento.',
  estado STRING COLLATE UTF8_BINARY COMMENT 'Sigla da UF do cliente, por exemplo SP, RJ, MG.',
  regiao STRING COLLATE UTF8_BINARY COMMENT 'Região do Brasil do cliente: Norte, Nordeste, Centro-Oeste, Sudeste ou Sul.',
  segmento_cliente STRING COLLATE UTF8_BINARY COMMENT 'Segmento do cliente no período: VIP, TOP_TIER ou REGULAR (mesma regra de gold.clientes_segmentacao).',
  quantidade BIGINT COMMENT 'Unidades vendidas nesta venda.',
  preco_unitario DECIMAL(10,2) COMMENT 'Preço cobrado por unidade, em reais (R$).',
  receita DECIMAL(10,2) COMMENT 'Receita bruta da venda em reais (R$) = quantidade × preço unitário. Somar para totalizar.',
  venda_antes_do_cadastro BOOLEAN COMMENT 'true quando a venda aconteceu antes da data de criação do produto (problema de qualidade de dados).')
COMMENT 'Uma linha por venda, com produto, cliente, região e segmento já juntos. Use para perguntas que cruzam dimensões, como receita por região e categoria, ou canal preferido de cada segmento. Inclui todas as vendas, mesmo de produtos não cadastrados. Período dos dados: 13/12/2025 a 11/01/2026.'
CLUSTER BY (data)
AS SELECT
  v.id_venda,
  v.data_venda,
  v.data,
  v.dia_semana,
  v.dia_semana_num,
  v.hora,
  v.canal_venda,
  v.id_produto,
  COALESCE(p.nome_produto, 'Produto não cadastrado') AS nome_produto,
  COALESCE(p.categoria, 'Não cadastrado')            AS categoria,
  COALESCE(p.marca, 'Não cadastrado')                AS marca,
  p.faixa_preco,
  v.produto_cadastrado,
  v.id_cliente,
  c.nome_cliente,
  c.estado,
  c.regiao,
  c.segmento_cliente,
  v.quantidade,
  v.preco_unitario,
  v.receita,
  v.venda_antes_do_cadastro
FROM silver.vendas v
LEFT JOIN silver.produtos p
  ON v.id_produto = p.id_produto
LEFT JOIN gold.clientes_segmentacao c
  ON v.id_cliente = c.id_cliente
