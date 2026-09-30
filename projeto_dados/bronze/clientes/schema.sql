CREATE TABLE projeto_dados.bronze.clientes (
  id_cliente STRING COLLATE UTF8_BINARY,
  nome_cliente STRING COLLATE UTF8_BINARY,
  estado STRING COLLATE UTF8_BINARY,
  pais STRING COLLATE UTF8_BINARY,
  data_cadastro TIMESTAMP)
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
