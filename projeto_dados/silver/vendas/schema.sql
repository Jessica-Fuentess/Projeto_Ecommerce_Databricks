CREATE MATERIALIZED VIEW `projeto_dados`.`silver`.`vendas` (
  id_produto STRING COLLATE UTF8_BINARY,
  id_venda STRING COLLATE UTF8_BINARY,
  data_venda TIMESTAMP,
  id_cliente STRING COLLATE UTF8_BINARY,
  canal_venda STRING COLLATE UTF8_BINARY,
  quantidade BIGINT,
  preco_unitario DECIMAL(10,2),
  receita DECIMAL(10,2),
  data DATE,
  hora INT,
  dia_semana_num INT,
  dia_semana STRING COLLATE UTF8_BINARY,
  produto_cadastrado BOOLEAN,
  venda_antes_do_cadastro BOOLEAN)
COMMENT 'Uma linha por venda, com receita, calendário e marcações de qualidade.'
AS 
