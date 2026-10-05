-- ============================================================================
-- BRONZE SCHEMA - Camada de Ingestão Bruta
-- ============================================================================
--
-- Descrição:
--   Estrutura das tabelas da camada Bronze do lakehouse de e-commerce.
--   A Bronze preserva os dados recebidos antes das transformações realizadas
--   na camada Silver.
--
-- Características:
--   • Dados brutos
--   • Estrutura próxima à origem
--   • Formato Delta Lake
--   • Sem regras de negócio aplicadas nesta camada
--   • Transformações e validações realizadas na Silver
--
-- Período dos dados: 13/12/2025 a 11/01/2026
-- Catálogo: projeto_dados
-- Schema: bronze
--
-- ============================================================================
CREATE CATALOG IF NOT EXISTS projeto_dados;
CREATE SCHEMA IF NOT EXISTS projeto_dados.bronze;
CREATE SCHEMA IF NOT EXISTS projeto_dados.silver;
CREATE SCHEMA IF NOT EXISTS projeto_dados.gold;
  
USE CATALOG projeto_dados;
USE SCHEMA bronze;

-- ============================================================================
-- 1. TABELA: clientes
-- ============================================================================

CREATE TABLE IF NOT EXISTS clientes (
    id_cliente STRING
        COMMENT 'Identificador único do cliente',

    nome_cliente STRING
        COMMENT 'Nome do cliente',

    estado STRING
        COMMENT 'Sigla da unidade federativa (UF)',

    pais STRING
        COMMENT 'País do cliente',

    data_cadastro TIMESTAMP
        COMMENT 'Data e hora de cadastro do cliente'
)
USING DELTA
COMMENT 'Dados brutos de clientes recebidos na camada Bronze.';

-- ============================================================================
-- 2. TABELA: produtos
-- ============================================================================

CREATE TABLE IF NOT EXISTS produtos (
    id_produto STRING
        COMMENT 'Identificador único do produto',

    nome_produto STRING
        COMMENT 'Nome do produto',

    categoria STRING
        COMMENT 'Categoria do produto',

    marca STRING
        COMMENT 'Marca do produto',

    preco_atual DOUBLE
        COMMENT 'Preço atual do produto em reais',

    data_criacao TIMESTAMP
        COMMENT 'Data e hora de criação do produto no catálogo'
)
USING DELTA
COMMENT 'Dados brutos de produtos recebidos na camada Bronze.';

-- ============================================================================
-- 3. TABELA: vendas
-- ============================================================================

CREATE TABLE IF NOT EXISTS vendas (
    id_venda STRING
        COMMENT 'Identificador único da venda',

    data_venda TIMESTAMP
        COMMENT 'Data e hora da venda',

    id_cliente STRING
        COMMENT 'Identificador do cliente',

    id_produto STRING
        COMMENT 'Identificador do produto',

    canal_venda STRING
        COMMENT 'Canal da venda: ecommerce ou loja_fisica',

    quantidade BIGINT
        COMMENT 'Quantidade de itens vendidos',

    preco_unitario DOUBLE
        COMMENT 'Preço unitário do produto no momento da venda'
)
USING DELTA
COMMENT 'Dados brutos de vendas recebidos na camada Bronze.';

-- ============================================================================
-- 4. TABELA: preco_competidores
-- ============================================================================

CREATE TABLE IF NOT EXISTS preco_competidores (
    id_produto STRING
        COMMENT 'Identificador do produto',

    nome_concorrente STRING
        COMMENT 'Nome do concorrente',

    preco_concorrente DOUBLE
        COMMENT 'Preço praticado pelo concorrente',

    data_coleta STRING
        COMMENT 'Data e hora da coleta do preço, preservada como texto na Bronze'
)
USING DELTA
COMMENT 'Dados brutos de preços coletados dos concorrentes.';

-- ============================================================================
-- RELACIONAMENTOS LÓGICOS
-- ============================================================================

-- clientes.id_cliente
--       ↑
--       └── vendas.id_cliente
--
-- produtos.id_produto
--       ↑
--       ├── vendas.id_produto
--       └── preco_competidores.id_produto
--
-- As relações são utilizadas nas transformações da camada Silver e Gold.
-- A Bronze não aplica integridade referencial nem regras de negócio.