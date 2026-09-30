CREATE MATERIALIZED VIEW `projeto_dados`.`silver`.`clientes` (
  estado STRING COLLATE UTF8_BINARY,
  id_cliente STRING COLLATE UTF8_BINARY,
  nome_cliente STRING COLLATE UTF8_BINARY,
  pais STRING COLLATE UTF8_BINARY,
  data_cadastro TIMESTAMP,
  nome_original STRING COLLATE UTF8_BINARY,
  nome_estado STRING COLLATE UTF8_BINARY,
  regiao STRING COLLATE UTF8_BINARY)
COMMENT 'Clientes com nome limpo, UF padronizada e região do IBGE.'
AS 
