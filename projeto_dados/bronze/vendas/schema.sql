CREATE TABLE projeto_dados.bronze.vendas (
  id_venda STRING COLLATE UTF8_BINARY,
  data_venda TIMESTAMP,
  id_cliente STRING COLLATE UTF8_BINARY,
  id_produto STRING COLLATE UTF8_BINARY,
  canal_venda STRING COLLATE UTF8_BINARY,
  quantidade BIGINT,
  preco_unitario DOUBLE)
USING delta
TBLPROPERTIES (
  'delta.enableDeletionVectors' = 'true',
  'delta.feature.appendOnly' = 'supported',
  'delta.feature.deletionVectors' = 'supported',
  'delta.feature.invariants' = 'supported',
  'delta.minReaderVersion' = '3',
  'delta.minWriterVersion' = '7',
  'delta.parquet.compression.codec' = 'zstd',
  'delta.parquet.format.version' = '2.12.0',
  'delta.parquet.format.version.afe.internal' = '2.12.0')
