CREATE TABLE projeto_dados.bronze.produtos (
  id_produto STRING COLLATE UTF8_BINARY,
  nome_produto STRING COLLATE UTF8_BINARY,
  categoria STRING COLLATE UTF8_BINARY,
  marca STRING COLLATE UTF8_BINARY,
  preco_atual DOUBLE,
  data_criacao TIMESTAMP)
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
