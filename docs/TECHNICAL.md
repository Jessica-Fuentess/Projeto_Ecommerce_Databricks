# 📘 Documentação Técnica

Detalhamento do projeto **E-commerce Lakehouse | Databricks**. Para a visão geral, volte ao [README](../README.md).

## Índice

1. [Bronze](#1-camada-bronze)
2. [Silver](#2-camada-silver)
3. [Gold](#3-camada-gold)
4. [Qualidade de dados](#4-qualidade-de-dados)
5. [Dashboard](#5-dashboard-executivo)
6. [Genie](#6-genie)
7. [Orquestração e pipeline](#7-orquestração-e-pipeline)
8. [Infrastructure as Code](#8-infrastructure-as-code)
9. [Conceitos aplicados](#9-conceitos-aplicados)

---

## 1. Camada Bronze

Dados de origem armazenados em tabelas Delta no Unity Catalog. Ingestão em `src/bronze/ingest.py`, que recebe o **caminho dos dados** e o **catálogo** como parâmetros, permitindo reutilização.

| Tabela | Descrição | Registros |
|---|---|---:|
| `bronze.clientes` | Dados brutos de clientes | 50 |
| `bronze.produtos` | Dados brutos de produtos | 215 |
| `bronze.vendas` | Dados brutos de vendas | 3.020 |
| `bronze.preco_competidores` | Preços coletados dos concorrentes | 728 |

---

## 2. Camada Silver

Transformações em **PySpark** com **Lakeflow Declarative Pipelines**.

### 👥 Clientes (`src/silver/clientes.py`)
- remoção de duplicidades e padronização dos nomes
- limpeza de títulos (`Sr.`, `Sra.`, `Dr.`, `Dra.`)
- padronização das UFs e identificação da região brasileira
- validação de campos obrigatórios

### 🛍️ Produtos (`src/silver/produtos.py`)
- remoção de duplicidades e padronização dos nomes
- conversão de preços para `DECIMAL`
- validação de identificadores e de preços positivos
- classificação por faixa de preço:

| Faixa | Regra |
|---|---|
| `BASICO` | Até R$ 500 |
| `MEDIO` | Acima de R$ 500 até R$ 1.000 |
| `PREMIUM` | Acima de R$ 1.000 |

### 💰 Vendas (`src/silver/vendas.py`)
- remoção de vendas duplicadas e conversão de tipos
- receita: `receita = quantidade × preco_unitario`
- atributos de calendário, dia da semana e hora da venda
- validação de canal, quantidade e preço
- identificação de **produtos não cadastrados** e de **vendas anteriores ao cadastro do produto**

### 🏷️ Preços dos concorrentes (`src/silver/preco_competidores.py`)
- remoção de duplicidades, padronização de preços e conversão da data de coleta
- relacionamento com os produtos
- marcação de preço **potencialmente suspeito** quando `preço do concorrente < 60% do nosso preço`

> Essa regra é um alerta de análise/qualidade, não uma confirmação de erro.

---

## 3. Camada Gold

### 📊 `gold.vendas_temporais`
Granularidade: **dia × hora × canal**. Métricas: quantidade de vendas, itens, receita e clientes únicos.

> ⚠️ Clientes únicos **não devem ser somados** entre linhas. Para clientes únicos em um período, use `COUNT DISTINCT` sobre `gold.vendas_detalhadas`.

### 🛍️ `gold.vendas_produtos`
Análise por produto: categoria, marca, quantidade de vendas, itens vendidos, receita, receita média, ranking global e ranking por categoria. Inclui vendas de produtos não cadastrados com identificação própria.

### 👤 `gold.clientes_segmentacao`
Segmentação por receita acumulada:

| Segmento | Critério |
|---|---|
| `VIP` | Receita ≥ R$ 22.000 |
| `TOP_TIER` | Receita ≥ R$ 17.000 e < R$ 22.000 |
| `REGULAR` | Receita < R$ 17.000 |

Também traz receita total, quantidade de compras, ticket médio, ranking, dados cadastrais e região.

### 🔎 `gold.vendas_detalhadas`
Uma linha por venda. Integra **Silver Vendas + Silver Produtos + Clientes Segmentação**. É a principal tabela do Genie para perguntas de clientes únicos por período.

### 💰 `gold.precos_competitividade`
Por produto: nosso preço, preço médio/menor/maior dos concorrentes, quantidade de concorrentes, diferença percentual vs. média e vs. menor preço, classificação de preço (menor que todos, maior que todos, dentro do intervalo etc.), indicador de preço suspeito, receita e itens vendidos.

Concorrentes: **Mercado Livre, Amazon, Magalu e Shopee**.

> Os preços dos concorrentes são um **snapshot de 11/01/2026**, não uma série histórica.

### 🧪 `gold.qualidade_dados`
Monitora: vendas de produtos não cadastrados, vendas anteriores ao cadastro, preços suspeitos, inconsistências de marca, nomes de produtos duplicados, produtos com menos de quatro concorrentes e necessidade de limpeza de títulos de clientes.

---

## 4. Qualidade de dados

Suíte em `tests/testes_qualidade.py`, cobrindo as tabelas Gold:

- schema, tipos e colunas obrigatórias
- granularidade e integridade entre tabelas
- valores esperados e regras de negócio
- completude e consistência

Há **tolerância para métricas numéricas**, evitando falsos positivos por ponto flutuante.

| Indicador | Resultado |
|---|---:|
| Clientes | 50 |
| Produtos | 215 |
| Vendas | 3.020 |
| Registros de concorrentes | 728 |
| Receita total | R$ 974.077,28 |
| Clientes VIP | 10 |
| Receita de clientes VIP | R$ 262.806,22 |
| Produtos monitorados | 215 |
| Produtos mais caros que todos os concorrentes | 35 |
| Vendas de produtos não cadastrados | 20 |
| Vendas anteriores ao cadastro do produto | 5 |
| Preços de concorrentes potencialmente suspeitos | 55 |

**Período:** vendas de 13/12/2025 a 11/01/2026; preços de concorrentes coletados em 11/01/2026.

---

## 5. Dashboard executivo

Arquivo: `dashboards/diretoria_ecommerce.lvdash.json` (Databricks AI/BI), com três áreas:

- **Vendas:** receita, quantidade de vendas, ticket médio, itens, receita diária, por dia da semana, por horário, top 10 produtos, filtros de período e canal.
- **Clientes:** quantidade, VIPs, receita VIP, distribuição por segmento, receita por região, ranking.
- **Preços:** produtos monitorados, mais caros que todos os concorrentes, diferença média, diferença por categoria, classificação de preços, alertas de preços suspeitos.

---

## 6. Genie

- Configuração: [`genie/diretoria_ecommerce.geniespace.json`](../genie/diretoria_ecommerce.geniespace.json)
- Documentação: [`docs/genie.md`](genie.md)
- **12 perguntas de benchmark validadas com 100% de acerto**
- Tabelas utilizadas:
  - `gold.clientes_segmentacao`
  - `gold.precos_competitividade`
  - `gold.vendas_detalhadas`
  - `gold.vendas_produtos`
  - `gold.vendas_temporais`

### Regra de clientes únicos

Para perguntas como "quantos clientes compraram no período?", o Genie usa `COUNT DISTINCT` sobre os identificadores de cliente em `gold.vendas_detalhadas`. Ele não soma a coluna de clientes únicos de `gold.vendas_temporais`, pois isso contaria o mesmo cliente mais de uma vez.

### Exemplos de perguntas validadas (6 das 12)

- Qual foi a receita total do e-commerce? *(retorna o canal e-commerce: R$ 705.486,21; o total com loja física é R$ 974.077,28)*
- Quais são os 10 produtos com maior receita?
- Quantos clientes VIP existem?
- Qual foi a receita por segmento de cliente?
- Quais produtos estão mais caros que todos os concorrentes?
- Quantos clientes realizaram compras no período?

---

## 7. Orquestração e pipeline

### Job (`resources/jobs.yml`)

`ingestao_bronze` → `executar_pipeline` → `testes_qualidade`

1. **ingestao_bronze:** executa `src/bronze/ingest.py`.
2. **executar_pipeline:** transformações Bronze → Silver → Gold.
3. **testes_qualidade:** executa `tests/testes_qualidade.py`; em caso de falha, retorna código de erro.

**Agendamento:** segunda a sexta, 06:00 (America/Sao_Paulo), atualmente **PAUSED** para evitar execuções desnecessárias no portfólio.

### Pipeline (`resources/pipeline.yml`)

| Configuração | Valor |
|---|---|
| Edition | `ADVANCED` |
| Channel | `CURRENT` |
| Compute | `Serverless` |
| Código | `src/silver/**` e `src/gold/**` |

---

## 8. Infrastructure as Code

Uso de **Databricks Asset Bundles** (`databricks.yml`), com recursos em `resources/` (`dashboards.yml`, `genie.yml`, `jobs.yml`, `pipeline.yml`). O GitHub guarda não só o código, mas também a configuração dos recursos. O bundle usa `engine: direct`.

---

## 9. Conceitos aplicados

- **Engenharia de Dados:** Lakehouse, Medallion, ETL/ELT, Delta Lake, pipelines, Jobs, Serverless, IaC
- **SQL:** `JOIN`, `GROUP BY`, `CASE`, CTEs, funções de janela, `ROW_NUMBER`, `COUNT DISTINCT`
- **PySpark:** DataFrames, joins, deduplicação, tratamento de tipos, validações, materialized views
- **Data Quality:** schema, integridade referencial, regras de negócio, completude, consistência
- **BI:** KPIs, segmentação de clientes, análises temporal, de produtos e de preços, dashboard e linguagem natural
