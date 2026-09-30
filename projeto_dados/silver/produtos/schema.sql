CREATE MATERIALIZED VIEW `projeto_dados`.`silver`.`produtos` (
  id_produto STRING COLLATE UTF8_BINARY,
  nome_produto STRING COLLATE UTF8_BINARY,
  categoria STRING COLLATE UTF8_BINARY,
  marca STRING COLLATE UTF8_BINARY,
  preco_atual DECIMAL(10,2),
  data_criacao TIMESTAMP,
  faixa_preco STRING COLLATE UTF8_BINARY)
COMMENT 'Catálogo de produtos limpo: preço em DECIMAL e faixa de preço.'
AS 
