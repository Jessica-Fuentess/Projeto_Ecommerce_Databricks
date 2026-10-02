# 🛒 Projeto E-commerce | Databricks Lakehouse

> Projeto completo de Engenharia de Dados desenvolvido com Databricks, PySpark e SQL, utilizando arquitetura Lakehouse e o modelo Medallion para transformar dados de e-commerce em informações confiáveis para análise e tomada de decisão.

---

## 📌 Sobre o projeto

Este projeto simula uma plataforma de dados para um negócio de e-commerce, desde a ingestão dos dados brutos até a disponibilização de informações analíticas para áreas de negócio.

A solução foi desenvolvida utilizando **Databricks**, **PySpark**, **SQL** e **Delta Lake**, seguindo uma arquitetura em camadas:

**Bronze → Silver → Gold**

O projeto contempla:

- ingestão de dados;
- tratamento e padronização;
- validações de qualidade;
- transformação e enriquecimento;
- modelagem analítica;
- segmentação de clientes;
- análise de vendas;
- análise de produtos;
- análise de competitividade de preços;
- testes automatizados;
- dashboard executivo;
- consultas utilizando Genie;
- orquestração de processos;
- infraestrutura como código.

O objetivo é demonstrar, em um único projeto, um fluxo próximo ao utilizado em ambientes reais de dados.

---

## 🎯 Objetivos

O projeto foi desenvolvido para responder perguntas de negócio como:

- Quanto o e-commerce está faturando?
- Como as vendas estão distribuídas ao longo do tempo?
- Quais produtos possuem maior volume de vendas?
- Quais clientes geram maior receita?
- Quantos clientes estão classificados como VIP?
- Como os preços praticados pela empresa se comparam aos concorrentes?
- Quais produtos possuem preços potencialmente suspeitos?
- Existem vendas de produtos não cadastrados?
- Existem vendas realizadas antes do cadastro do produto?
- Os dados possuem problemas de qualidade que precisam de atenção?

---

## 🏗️ Arquitetura

A solução utiliza uma arquitetura **Lakehouse**, organizada pelo modelo **Medallion**.

**Fluxo principal:**

**Dados de origem → Ingestão → Bronze → Silver → Gold → Consumo**

### Componentes

- **Dados de origem:** arquivos CSV;
- **Ingestão:** processo Python responsável pelo carregamento dos dados;
- **Bronze:** dados brutos armazenados em Delta;
- **Silver:** dados tratados, padronizados e validados;
- **Gold:** dados preparados para análises de negócio;
- **Dashboard:** Databricks AI/BI;
- **Genie:** consultas em linguagem natural;
- **Testes:** validações automatizadas de qualidade;
- **Jobs:** orquestração do fluxo de processamento.

---

## 🥉 Camada Bronze

A camada Bronze recebe os dados de origem e os armazena em tabelas Delta dentro do Unity Catalog.

### Tabelas

| Tabela | Descrição | Registros |
|---|---|---:|
| `bronze.clientes` | Dados brutos de clientes | 50 |
| `bronze.produtos` | Dados brutos de produtos | 215 |
| `bronze.vendas` | Dados brutos de vendas | 3.020 |
| `bronze.preco_competidores` | Preços coletados dos concorrentes | 728 |

### Ingestão

Arquivo responsável:

`src/bronze/ingest.py`

O processo recebe o caminho dos dados e o catálogo como parâmetros, permitindo que a ingestão seja executada de forma reutilizável.

---

## 🥈 Camada Silver

A camada Silver transforma os dados brutos em informações mais confiáveis e padronizadas.

As transformações são implementadas com **PySpark** e **Lakeflow Declarative Pipelines**.

### 👥 Clientes

Arquivo:

`src/silver/clientes.py`

Principais tratamentos:

- remoção de duplicidades;
- padronização dos nomes;
- limpeza de títulos como `Sr.`, `Sra.`, `Dr.` e `Dra.`;
- padronização das UFs;
- identificação da região brasileira;
- validação de campos obrigatórios.

---

### 🛍️ Produtos

Arquivo:

`src/silver/produtos.py`

Principais tratamentos:

- remoção de duplicidades;
- padronização dos nomes;
- conversão de preços para `DECIMAL`;
- classificação por faixa de preço;
- validação de identificadores;
- validação de preços positivos.

### Faixas de preço

| Faixa | Regra |
|---|---|
| `BASICO` | Até R$ 500 |
| `MEDIO` | Acima de R$ 500 até R$ 1.000 |
| `PREMIUM` | Acima de R$ 1.000 |

---

### 💰 Vendas

Arquivo:

`src/silver/vendas.py`

Principais tratamentos:

- remoção de vendas duplicadas;
- conversão de tipos;
- cálculo da receita;
- criação de atributos de calendário;
- identificação do dia da semana;
- identificação da hora da venda;
- validação do canal;
- validação de quantidade;
- validação de preço;
- identificação de produtos não cadastrados;
- identificação de vendas realizadas antes do cadastro do produto.

A receita é calculada como:

`receita = quantidade × preco_unitario`

---

### 🏷️ Preços dos concorrentes

Arquivo:

`src/silver/preco_competidores.py`

Principais tratamentos:

- remoção de duplicidades;
- padronização dos preços;
- conversão da data de coleta;
- relacionamento com os produtos;
- identificação de preços potencialmente suspeitos.

Um preço é marcado como potencialmente suspeito quando:

`preço do concorrente < 60% do nosso preço`

Essa regra é utilizada como alerta de qualidade/análise e não como confirmação de erro.

---

# 🥇 Camada Gold

A camada Gold concentra as informações preparadas para análise de negócio.

## 📊 `gold.vendas_temporais`

Tabela com granularidade:

`dia × hora × canal`

Principais métricas:

- quantidade de vendas;
- quantidade de itens;
- receita;
- clientes únicos.

Essa tabela permite analisar o comportamento das vendas ao longo do tempo.

> A métrica de clientes únicos não deve ser somada entre diferentes linhas da tabela. Para obter clientes únicos em um período, a contagem deve ser realizada sobre os identificadores de clientes na tabela de vendas detalhadas.

---

## 🛍️ `gold.vendas_produtos`

Tabela analítica por produto vendido.

Principais informações:

- produto;
- categoria;
- marca;
- quantidade de vendas;
- itens vendidos;
- receita;
- receita média;
- ranking global;
- ranking por categoria.

Também contempla vendas de produtos que não foram encontrados no cadastro, utilizando uma identificação apropriada para esses casos.

---

## 👤 `gold.clientes_segmentacao`

Tabela utilizada para análise e segmentação dos clientes.

Os clientes são classificados de acordo com a receita acumulada:

| Segmento | Critério |
|---|---|
| `VIP` | Receita ≥ R$ 22.000 |
| `TOP_TIER` | Receita ≥ R$ 17.000 e < R$ 22.000 |
| `REGULAR` | Receita < R$ 17.000 |

A tabela também disponibiliza informações como:

- receita total;
- quantidade de compras;
- ticket médio;
- ranking de clientes;
- segmento;
- informações cadastrais;
- informações regionais.

---

## 🔎 `gold.vendas_detalhadas`

Tabela detalhada com granularidade de uma linha por venda.

Integra informações de:

**Silver Vendas + Silver Produtos + Clientes Segmentação**

É utilizada para análises que exigem cruzamento entre diferentes dimensões.

Também é a principal tabela utilizada pelo Genie para perguntas que envolvem clientes únicos em determinado período.

---

## 💰 `gold.precos_competitividade`

Tabela utilizada para análise de posicionamento de preços.

Para cada produto são disponibilizadas informações como:

- nosso preço;
- preço médio dos concorrentes;
- menor preço;
- maior preço;
- quantidade de concorrentes;
- diferença percentual em relação à média;
- diferença percentual em relação ao menor preço;
- classificação de preço;
- indicador de preço potencialmente suspeito;
- receita;
- itens vendidos.

### Concorrentes

Os concorrentes considerados são:

- Mercado Livre;
- Amazon;
- Magalu;
- Shopee.

### Classificação de preço

A tabela permite identificar situações como:

- preço menor que todos os concorrentes;
- preço maior que todos os concorrentes;
- preço dentro do intervalo dos concorrentes;
- outras situações de posicionamento.

> Os dados de concorrentes representam um snapshot coletado em **11/01/2026**. Portanto, a análise representa o posicionamento de preços nesse momento e não uma série histórica diária.

---

## 🧪 `gold.qualidade_dados`

Tabela destinada ao monitoramento de regras de qualidade e consistência dos dados.

Entre as situações verificadas estão:

- vendas de produtos não cadastrados;
- vendas anteriores ao cadastro do produto;
- preços de concorrentes potencialmente suspeitos;
- inconsistências de marca;
- nomes de produtos duplicados;
- produtos com menos de quatro concorrentes;
- necessidade de limpeza de títulos de clientes.

---

# 🧪 Qualidade de dados

O projeto possui uma suíte de testes automatizados localizada em:

`tests/testes_qualidade.py`

Os testes verificam diferentes aspectos das tabelas Gold, incluindo:

- schema;
- tipos de dados;
- colunas obrigatórias;
- granularidade;
- integridade entre tabelas;
- valores esperados;
- regras de negócio;
- completude;
- consistência;
- qualidade dos dados.

Os testes também possuem tolerância para métricas numéricas, evitando que pequenas diferenças de ponto flutuante gerem falsos positivos.

---

## 📋 Principais resultados de qualidade

Com os dados atuais:

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

---

# 📅 Período dos dados

Os dados de vendas utilizados no projeto abrangem:

**13/12/2025 → 11/01/2026**

Os dados de preços dos concorrentes correspondem a uma coleta realizada em:

**11/01/2026**

---

# 📊 Dashboard Executivo

O projeto possui um dashboard desenvolvido no **Databricks AI/BI**.

Arquivo:

`dashboards/diretoria_ecommerce.lvdash.json`

O dashboard está dividido em três áreas principais.

### 📈 Vendas

Indicadores e análises como:

- receita;
- quantidade de vendas;
- ticket médio;
- itens vendidos;
- receita diária;
- receita por dia da semana;
- vendas por horário;
- top 10 produtos;
- filtros por período;
- filtros por canal.

### 👥 Clientes

Indicadores e análises como:

- quantidade de clientes;
- quantidade de clientes VIP;
- receita dos clientes VIP;
- distribuição por segmento;
- receita por região;
- ranking de clientes.

### 💰 Preços

Indicadores e análises como:

- produtos monitorados;
- produtos mais caros que todos os concorrentes;
- diferença média de preço;
- diferença por categoria;
- classificação de preços;
- alertas relacionados a preços potencialmente suspeitos.

---

# 🤖 Genie

O projeto também utiliza **Databricks Genie** para permitir consultas em linguagem natural sobre os dados.

Configuração:

`genie/diretoria_ecommerce.geniespace.json`

Documentação:

`docs/genie.md`

O Genie utiliza cinco tabelas Gold:

- `gold.clientes_segmentacao`
- `gold.precos_competitividade`
- `gold.vendas_detalhadas`
- `gold.vendas_produtos`
- `gold.vendas_temporais`

### Exemplos de perguntas

- Qual foi a receita total do e-commerce?
- Quais são os 10 produtos com maior receita?
- Quantos clientes VIP existem?
- Qual foi a receita por segmento de cliente?
- Quais produtos estão mais caros que todos os concorrentes?
- Quantos clientes realizaram compras no período?

As instruções do Genie também definem como realizar análises de clientes únicos, evitando contar linhas de forma incorreta.

---

# ⚙️ Orquestração

O projeto possui um Job responsável por organizar a execução do fluxo de dados.

Arquivo:

`resources/jobs.yml`

### Fluxo

**1. ingestao_bronze**

↓  

**2. executar_pipeline**

↓  

**3. testes_qualidade**

### 1. Ingestão Bronze

Executa:

`src/bronze/ingest.py`

Responsável por carregar os dados de origem para a camada Bronze.

### 2. Pipeline

Executa o pipeline responsável pelas transformações:

**Bronze → Silver → Gold**

### 3. Testes

Executa:

`tests/testes_qualidade.py`

Caso os testes falhem, o processo retorna código de erro.

---

## 🕐 Agendamento

O Job foi configurado para execução:

**Segunda a sexta-feira às 06:00 — America/Sao_Paulo**

O agendamento está atualmente:

**PAUSED**

Essa configuração foi mantida dessa forma para o projeto de portfólio, evitando execuções automáticas desnecessárias.

---

# 🔧 Pipeline

Arquivo:

`resources/pipeline.yml`

### Configuração principal

| Configuração | Valor |
|---|---|
| Edition | `ADVANCED` |
| Channel | `CURRENT` |
| Compute | `Serverless` |

O pipeline utiliza os códigos das camadas:

- `src/silver/**`
- `src/gold/**`

---

# 🏗️ Infrastructure as Code

O projeto utiliza **Databricks Asset Bundles** para estruturar e versionar a configuração da solução.

Arquivo principal:

`databricks.yml`

### Recursos

- `resources/dashboards.yml`
- `resources/genie.yml`
- `resources/jobs.yml`
- `resources/pipeline.yml`

Essa abordagem permite manter no GitHub não apenas o código de transformação, mas também a configuração da infraestrutura e dos recursos utilizados pelo projeto.

O Bundle utiliza:

`engine: direct`

para permitir o gerenciamento dos recursos compatíveis com o mecanismo de implantação direta.

---

# 📁 Estrutura do projeto

Projeto_Ecommerce_Databricks/

├── data/

│   ├── clientes.csv

│   ├── produtos.csv

│   ├── vendas.csv

│   └── preco_competidores.csv

│

├── src/

│   ├── bronze/

│   │   ├── bronze_schema.sql

│   │   └── ingest.py

│   │

│   ├── silver/

│   │   ├── clientes.py

│   │   ├── preco_competidores.py

│   │   ├── produtos.py

│   │   └── vendas.py

│   │

│   └── gold/

│       ├── clientes_segmentacao.sql

│       ├── precos_competitividade.sql

│       ├── qualidade_dados.sql

│       ├── vendas_detalhadas.sql

│       ├── vendas_produtos.sql

│       └── vendas_temporais.sql

│

├── tests/

│   └── testes_qualidade.py

│

├── dashboards/

│   └── diretoria_ecommerce.lvdash.json

│

├── genie/

│   └── diretoria_ecommerce.geniespace.json

│

├── docs/

│   ├── architecture.md

│   └── genie.md

│

├── resources/

│   ├── dashboards.yml

│   ├── genie.yml

│   ├── jobs.yml

│   └── pipeline.yml

│

├── .gitignore

├── .gitattributes

├── databricks.yml

└── README.md

---

# 🛠️ Tecnologias utilizadas

![Databricks](https://img.shields.io/badge/Databricks-EF3A2D?style=for-the-badge&logo=databricks&logoColor=white)
![PySpark](https://img.shields.io/badge/PySpark-FDEE21?style=for-the-badge&logo=apache-spark&logoColor=black)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![SQL](https://img.shields.io/badge/SQL-336791?style=for-the-badge&logo=postgresql&logoColor=white)
![Delta Lake](https://img.shields.io/badge/Delta_Lake-00ADD8?style=for-the-badge)
![Git](https://img.shields.io/badge/Git-F05032?style=for-the-badge&logo=git&logoColor=white)
![GitHub](https://img.shields.io/badge/GitHub-181717?style=for-the-badge&logo=github&logoColor=white)

### Principais tecnologias e recursos

- Databricks
- Unity Catalog
- Delta Lake
- PySpark
- SQL
- Lakeflow Declarative Pipelines
- Databricks Asset Bundles
- Databricks Jobs
- Databricks AI/BI
- Genie
- Python
- Git
- GitHub

---

# 🧠 Conceitos aplicados

Este projeto demonstra conhecimentos em:

### Engenharia de Dados

- arquitetura Lakehouse;
- arquitetura Medallion;
- ingestão de dados;
- ETL/ELT;
- transformação de dados;
- Delta Lake;
- pipelines;
- Jobs;
- orquestração;
- Serverless;
- Infrastructure as Code.

### SQL

- `JOIN`;
- `GROUP BY`;
- `CASE`;
- agregações;
- funções de janela;
- `COUNT DISTINCT`;
- `ROW_NUMBER`;
- CTEs;
- cálculos de métricas;
- modelagem analítica.

### PySpark

- DataFrames;
- transformação de dados;
- funções Spark SQL;
- joins;
- deduplicação;
- tratamento de tipos;
- criação de colunas;
- validações;
- materialized views.

### Data Quality

- validação de schema;
- integridade referencial;
- regras de negócio;
- validação de valores;
- completude;
- consistência;
- testes automatizados.

### Business Intelligence

- KPIs;
- segmentação de clientes;
- análise temporal;
- análise de produtos;
- análise de preços;
- dashboard executivo;
- consultas em linguagem natural.

---

# 📈 Resultados

O projeto atualmente trabalha com:

- **50 clientes**
- **215 produtos**
- **3.020 vendas**
- **728 registros de preços de concorrentes**
- **R$ 974.077,28 em receita**
- **10 clientes VIP**
- **R$ 262.806,22 de receita dos clientes VIP**
- **215 produtos monitorados**
- **35 produtos mais caros que todos os concorrentes**

Esses resultados são utilizados como referências nos testes automatizados de qualidade.

---

# 💼 O que este projeto demonstra

Este projeto foi desenvolvido para demonstrar a aplicação prática de conceitos de **Engenharia de Dados, Analytics e Business Intelligence** em um cenário de negócio.

Entre os principais conhecimentos demonstrados estão:

- construção de um Lakehouse;
- utilização da arquitetura Medallion;
- desenvolvimento de pipelines com PySpark;
- utilização de SQL para transformação e análise;
- criação de camadas Bronze, Silver e Gold;
- implementação de regras de qualidade;
- criação de testes automatizados;
- modelagem de dados para análise;
- criação de indicadores de negócio;
- análise de comportamento de clientes;
- análise de produtos;
- análise de competitividade de preços;
- criação de dashboards;
- utilização de IA para consulta aos dados;
- orquestração de processos;
- versionamento de código;
- Infrastructure as Code.

---

# 📚 Documentação

Documentação complementar disponível no projeto.

### Arquitetura

`docs/architecture.md`

Contém a visão geral da arquitetura, fluxo de dados, camadas e componentes do projeto.

### Genie

`docs/genie.md`

Contém as tabelas utilizadas pelo Genie, regras de negócio, relacionamentos e exemplos de consultas.

---

# 🚀 Próximos passos

Possíveis evoluções para o projeto:

- adicionar novos períodos de dados;
- criar histórico de preços dos concorrentes;
- implementar novas métricas comerciais;
- ampliar as regras de qualidade;
- adicionar novos dashboards;
- incluir novos canais de vendas;
- criar análises de retenção e recorrência;
- implementar análises mais avançadas de comportamento dos clientes;
- evoluir o processo de ingestão para fontes externas.

---

# 👩‍💻 Autora

**Jéssica Fuentes**

**Analista de Dados | Business Intelligence**

Experiência profissional em Comércio Exterior, Logística e Operações, em transição de carreira para a área de Tecnologia e Dados.

Atualmente direcionada para oportunidades em:

- Data Analytics
- Business Intelligence
- Data Engineering
- BI Analytics
- CRM Analytics

### Principais tecnologias

`SQL` · `Power BI` · `Python` · `PySpark` · `Databricks` · `Excel` · `Git` · `GitHub`

---

## ⭐ Sobre o projeto

Este projeto faz parte do meu portfólio profissional e foi desenvolvido com foco na aplicação prática de conceitos de **Dados, Engenharia de Dados, BI e Cloud Data Platforms**.

Se este projeto foi útil ou interessante, considere deixar uma ⭐ no repositório.
