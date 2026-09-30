CREATE MATERIALIZED VIEW `projeto_dados`.`silver`.`preco_competidores` (
  id_produto STRING COLLATE UTF8_BINARY,
  nome_concorrente STRING COLLATE UTF8_BINARY,
  preco_concorrente DECIMAL(10,2),
  data_coleta TIMESTAMP,
  preco_suspeito BOOLEAN)
COMMENT 'Preço de cada concorrente por produto, com marcação de preço suspeito.'
AS 
