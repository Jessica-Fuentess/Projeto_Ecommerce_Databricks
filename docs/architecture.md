# Arquitetura do Lakehouse E-commerce

Documentação técnica da arquitetura end-to-end do projeto de Data Lakehouse.

---

## Visão Geral

### Objetivo

Implementar um Data Lakehouse para análise de dados de e-commerce, desde a ingestão dos dados brutos até o consumo analítico por meio de dashboards e consultas em linguagem natural com o Genie.

A arquitetura utiliza o padrão Medallion, separando o processamento em três camadas:

- **Bronze:** dados brutos, próximos à origem;
- **Silver:** dados tratados, enriquecidos e validados;
- **Gold:** dados preparados para análise e consumo pelas áreas de negócio.

O projeto também contempla qualidade de dados, testes automatizados, governança com Unity Catalog e infraestrutura como código utilizando Databricks Asset Bundles.

### Princípios de Design

- Arquitetura Medallion (Bronze → Silver → Gold)
- Infrastructure as Code com Databricks Asset Bundles
- Qualidade de dados com Expectations e testes automatizados
- Serverless Compute
- Governança com Unity Catalog
- Dados Gold orientados a casos de uso de negócio
- Self-Service Analytics com AI/BI Dashboard e Genie

---

## Arquitetura Geral

```text
┌──────────────────────────────────────────────┐
│              DADOS DE ORIGEM                 │
│                                              │
│  clientes.csv                                │
│  produtos.csv                                │
│  vendas.csv                                  │
│  preco_competidores.csv                      │
└──────────────────────┬───────────────────────┘
                       │
                       ↓
┌──────────────────────────────────────────────┐
│                   INGESTÃO                   │
│                                              │
│  leitura dos CSVs                            │
│  conversão dos tipos                         │
│  carga das tabelas Bronze                    │
└──────────────────────┬───────────────────────┘
                       │
                       ↓
┌──────────────────────────────────────────────┐
│                  BRONZE                      │
│                                              │
│          projeto_dados.bronze                │
│                                              │
│  • Dados brutos                              │
│  • Estrutura próxima à origem                │
│  • Formato Delta Lake                        │
│  • Sem regras de negócio                     │
└──────────────────────┬───────────────────────┘
                       │
                       ↓
┌──────────────────────────────────────────────┐
│                  SILVER                      │
│                                              │
│          projeto_dados.silver                │
│                                              │
│  • Limpeza                                   │
│  • Padronização                              │
│  • Enriquecimento                            │
│  • Validação                                 │
│  • Regras de qualidade                       │
│                                              │
│  PySpark + Lakeflow                         │
└──────────────────────┬───────────────────────┘
                       │
                       ↓
┌──────────────────────────────────────────────┐
│                   GOLD                       │
│                                              │
│           projeto_dados.gold                 │
│                                              │
│  • Agregações                                │
│  • Métricas de negócio                       │
│  • Rankings                                  │
│  • Segmentação                               │
│  • Análise de competitividade                │
│                                              │
│  Databricks SQL + Materialized Views         │
└───────────────┬──────────────┬───────────────┘
                │              │
                ↓              ↓
      ┌────────────────┐  ┌────────────────┐
      │   AI/BI        │  │     Genie      │
      │   Dashboard    │  │     Space      │
      │                │  │                │
      │ Visão gerencial│  │ Linguagem      │
      │ do e-commerce  │  │ natural        │
      └────────────────┘  └────────────────┘
                │
                ↓
      ┌──────────────────────┐
      │ Testes de Qualidade  │
      │ e Validação          │
      └──────────────────────┘
```

---

# Stack Tecnológico

| Componente | Tecnologia | Aplicação |
|---|---|---|
| Lakehouse | Delta Lake | Armazenamento das tabelas |
| Governança | Unity Catalog | Catálogo e organização dos dados |
| Pipeline | Lakeflow Spark Declarative Pipelines | Transformações Silver e Gold |
| Compute | Serverless | Execução do pipeline e consultas |
| Orquestração | Lakeflow Jobs | Agendamento do pipeline |
| Silver | Python / PySpark | Limpeza, enriquecimento e qualidade |
| Gold | Databricks SQL | Modelagem analítica |
| BI | AI/BI Dashboards | Visualização dos indicadores |
| IA | Genie Space | Consultas em linguagem natural |
| Testes | Python / PySpark | Validação dos dados |
| Deploy | Databricks Asset Bundles | Infrastructure as Code |
| Versionamento | Git / GitHub | Código e configuração |

---

# Camada Bronze

## Propósito

A camada Bronze armazena os dados brutos recebidos das fontes de origem, mantendo uma estrutura próxima à original.

A Bronze não aplica regras de negócio ou transformações analíticas.

## Características

- Dados brutos
- Estrutura próxima à origem
- Formato Delta Lake
- Sem regras de negócio
- Sem validações analíticas
- Base para processamento da camada Silver

## Tabelas

| Tabela | Colunas | Propósito |
|---|---:|---|
| `clientes` | 5 | Cadastro de clientes |
| `produtos` | 6 | Catálogo de produtos |
| `vendas` | 7 | Transações de vendas |
| `preco_competidores` | 4 | Preços coletados dos concorrentes |

## Schema

A definição das tabelas Bronze está documentada em:

```text
src/bronze/bronze_schema.sql
```

As tabelas utilizam Delta Lake.

## Decisões de Design

### Por que utilizar Delta Lake?

A utilização de Delta Lake mantém a camada Bronze consistente com as demais camadas do Lakehouse e permite recursos como:

- transações ACID;
- histórico de dados;
- evolução de schema;
- integração nativa com o ecossistema Databricks.

### Por que manter a Bronze próxima à origem?

A separação permite preservar os dados recebidos antes das transformações realizadas na Silver.

Isso facilita:

- rastreabilidade;
- auditoria;
- reprocessamento;
- identificação de problemas na origem.

---

# Camada Silver

## Propósito

A camada Silver transforma os dados brutos em dados tratados, padronizados, enriquecidos e validados.

É a camada utilizada como base confiável para a construção das tabelas Gold.

## Características

- Remoção de duplicidades
- Padronização de textos
- Conversão de tipos
- Enriquecimento de informações
- Criação de métricas derivadas
- Validação de qualidade
- Marcação de registros problemáticos
- Materialized Views

## Transformações

### `clientes.py`

Principais transformações:

- Remove duplicidades por `id_cliente`;
- Preserva o nome original em `nome_original`;
- Remove pronomes de tratamento como `Sr.`, `Sra.`, `Srta.`, `Dr.` e `Dra.`;
- Padroniza o nome do cliente;
- Normaliza a UF;
- Adiciona `nome_estado`;
- Adiciona `regiao`.

O mapeamento de estados utiliza as 27 unidades federativas brasileiras.

### `produtos.py`

Principais transformações:

- Remove duplicidades por `id_produto`;
- Remove espaços desnecessários do nome do produto;
- Converte `preco_atual` para `DECIMAL(10,2)`;
- Cria a classificação `faixa_preco`;
- Valida identificador e preço.

As faixas de preço são:

- `BASICO`
- `MEDIO`
- `PREMIUM`

### `vendas.py`

Principais transformações:

- Remove duplicidades por `id_venda`;
- Converte `preco_unitario` para `DECIMAL(10,2)`;
- Calcula `receita`;
- Cria campos de calendário;
- Cria o dia da semana em português;
- Verifica se o produto está cadastrado;
- Identifica vendas realizadas antes do cadastro do produto.

Também são aplicadas regras de qualidade para:

- campos obrigatórios;
- quantidade positiva;
- preço positivo;
- canal de venda conhecido.

### `preco_competidores.py`

Principais transformações:

- Remove duplicidades por `id_produto` e `nome_concorrente`;
- Converte o preço do concorrente para `DECIMAL(10,2)`;
- Converte `data_coleta` para timestamp;
- Relaciona o preço do concorrente ao preço do produto;
- Identifica preços potencialmente suspeitos.

Um preço é marcado como suspeito quando:

```text
preço do concorrente < 60% do preço do produto
```

O registro não é descartado. O problema é marcado para permitir análise posterior.

---

# Qualidade de Dados na Silver

A camada Silver utiliza Expectations do Lakeflow para validar os dados.

Existem dois comportamentos principais.

### Expectations críticas

Utilizadas quando a violação deve impedir a continuidade do processamento.

Exemplo:

```python
@dp.expect_all_or_fail({
    "id_cliente_preenchido": "id_cliente IS NOT NULL",
    "preco_positivo": "preco_atual > 0"
})
```

### Expectations de observação

Utilizadas para problemas que devem ser identificados, mas não necessariamente interromper o pipeline.

Exemplo:

```python
@dp.expect_all({
    "produto_cadastrado": "produto_cadastrado",
    "preco_plausivel": "NOT preco_suspeito"
})
```

Essa abordagem permite manter os registros para análise e, ao mesmo tempo, tornar os problemas observáveis.

---

# Camada Gold

## Propósito

A camada Gold contém dados preparados para consumo analítico.

As tabelas são construídas de acordo com perguntas e necessidades de negócio específicas.

## Características

- Agregações;
- Métricas de negócio;
- Rankings;
- Segmentação;
- Análises temporais;
- Análises de produtos;
- Análises de clientes;
- Análises de preços;
- Materialized Views;
- SQL como linguagem principal.

---

## Tabelas Gold

### 1. `vendas_temporais`

**Pergunta de negócio:**

> Como as vendas se distribuem ao longo do tempo?

### Granularidade

Uma linha por:

```text
data × hora × canal
```

### Principais métricas

- total de vendas;
- itens vendidos;
- receita;
- clientes distintos.

### Uso

- análise temporal;
- comparação entre canais;
- identificação de horários de maior movimentação;
- análise de comportamento das vendas.

---

### 2. `vendas_produtos`

**Pergunta de negócio:**

> Quais produtos apresentam maior volume de vendas e receita?

### Granularidade

Uma linha por produto vendido.

### Principais informações

- produto;
- categoria;
- quantidade vendida;
- receita;
- ticket médio;
- ranking global;
- ranking dentro da categoria.

### Uso

- ranking de produtos;
- análise por categoria;
- identificação de produtos de maior receita;
- análise de volume vendido.

---

### 3. `vendas_detalhadas`

**Pergunta de negócio:**

> Como analisar cada venda individualmente combinando informações de diferentes dimensões?

### Granularidade

Uma linha por venda.

### Relacionamentos

A tabela combina informações provenientes de:

- `silver.vendas`;
- `silver.produtos`;
- `gold.clientes_segmentacao`.

### Uso

- análises detalhadas;
- cruzamento entre vendas, produtos e clientes;
- drill-down;
- consultas analíticas mais específicas.

---

### 4. `clientes_segmentacao`

**Pergunta de negócio:**

> Como os clientes se distribuem em relação ao valor gerado?

### Granularidade

Uma linha por cliente.

### Segmentação

| Segmento | Regra |
|---|---|
| `VIP` | Receita >= R$ 22.000 |
| `TOP_TIER` | Receita >= R$ 17.000 e < R$ 22.000 |
| `REGULAR` | Receita < R$ 17.000 |

### Principais métricas

- total de compras;
- receita;
- ticket médio;
- primeira compra;
- última compra;
- segmento;
- ranking de receita;
- estado;
- região.

### Uso

- segmentação de clientes;
- análise de valor dos clientes;
- análises de Customer Success;
- identificação de clientes de maior receita.

Clientes sem compras permanecem na tabela devido ao uso de `LEFT JOIN` a partir da dimensão de clientes.

---

### 5. `precos_competitividade`

**Pergunta de negócio:**

> Como os preços dos produtos se posicionam em relação aos concorrentes?

### Granularidade

Uma linha por produto.

### Principais informações

- preço próprio;
- média dos preços dos concorrentes;
- menor preço concorrente;
- maior preço concorrente;
- quantidade de concorrentes;
- classificação de preço;
- diferença percentual em relação à média;
- indicador de preço suspeito;
- receita;
- quantidade vendida.

### Classificação competitiva

A tabela classifica o posicionamento do produto em relação ao mercado, incluindo situações como:

- mais caro que todos;
- mais barato que todos;
- acima da média;
- abaixo da média;
- próximo da média.

### Uso

- análise do posicionamento de preços;
- análise de competitividade;
- identificação de produtos com maior diferença de preço;
- apoio à análise comercial.

---

# Por que utilizar SQL na Gold?

As transformações da Gold são predominantemente analíticas, envolvendo:

- `SUM`;
- `COUNT`;
- `AVG`;
- `GROUP BY`;
- `JOIN`;
- funções de janela;
- classificações e agregações.

SQL facilita a leitura das regras de negócio e permite que analistas e profissionais de BI compreendam e revisem a lógica com maior facilidade.

---

# Orquestração

## Lakeflow Pipeline

O pipeline é responsável pela transformação das camadas Silver e Gold.

### Configuração

- Edição: `ADVANCED`
- Compute: `Serverless`
- Canal: `CURRENT`
- Catálogo: `${var.catalogo}`
- Schema: `silver`

O código utilizado pelo pipeline está localizado em:

```text
src/
├── silver/
└── gold/
```

O recurso é configurado em:

```text
resources/pipeline.yml
```

---

## Fluxo de execução

```text
Bronze
   ↓
Silver
   ↓
Gold
```

As dependências entre as tabelas são determinadas pelo pipeline a partir das referências utilizadas no código.

---

# Lakeflow Job

O projeto possui um Job responsável por orquestrar a ingestão, a transformação e a validação dos dados.

### Configuração

- Nome: `Lakehouse E-commerce - Atualização Diária`
- Horário configurado: 06:00
- Fuso horário: `America/Sao_Paulo`
- Frequência: segunda a sexta-feira
- Concorrência máxima: 1 execução
- Timeout: 1 hora
- `full_refresh`: `false`

O Job está configurado como **pausado** no ambiente versionado do projeto para evitar execuções automáticas durante o desenvolvimento.

A configuração está em:

```text
resources/jobs.yml
```

### Fluxo de execução

```text
1. ingestao_bronze
   ↓
2. executar_pipeline
   ↓
3. testes_qualidade
```text

---

# Analytics e Consumo

## AI/BI Dashboard

O projeto possui um dashboard destinado à análise gerencial do e-commerce.

### Arquivo

```text
dashboards/diretoria_ecommerce.lvdash.json
```

### Principais áreas

#### Vendas

- receita;
- vendas;
- ticket médio;
- itens vendidos;
- receita por canal;
- análise temporal;
- ranking de produtos.

#### Clientes

- quantidade de clientes;
- segmentação;
- receita por segmento;
- receita por região;
- ranking de clientes.

#### Pricing

- produtos monitorados;
- posicionamento de preços;
- produtos mais caros que todos os concorrentes;
- diferença de preço em relação à média;
- indicadores de competitividade.

A configuração de implantação do dashboard está em:

```text
resources/dashboards.yml
```

---

# Genie Space

O projeto também utiliza um Genie Space para permitir consultas em linguagem natural sobre as tabelas Gold.

### Nome

```text
Diretoria E-commerce 2026
```

### Idioma

Português (Brasil)

### Fontes

O Genie utiliza as tabelas Gold:

```text
projeto_dados.gold.vendas_temporais
projeto_dados.gold.vendas_produtos
projeto_dados.gold.vendas_detalhadas
projeto_dados.gold.clientes_segmentacao
projeto_dados.gold.precos_competitividade
```

### Exemplos de perguntas

- Qual foi a receita total do período?
- Quais são os 10 produtos com maior receita?
- Quantos clientes são VIP?
- Qual região concentra a maior receita?
- Quantos produtos estão mais caros que todos os concorrentes?
- Qual é a diferença média de preço em relação aos concorrentes?

A documentação do Genie está em:

```text
docs/genie.md
```

A definição serializada do Space poderá ser versionada em:

```text
genie/diretoria_ecommerce.geniespace.json
```

O recurso de implantação está configurado em:

```text
resources/genie.yml
```

---

# Qualidade de Dados e Testes

A estratégia de qualidade ocorre em diferentes níveis.

## Silver

As Expectations verificam regras críticas e problemas conhecidos durante o processamento.

Exemplos:

- identificadores obrigatórios;
- preços positivos;
- quantidades positivas;
- canais conhecidos;
- existência do produto;
- plausibilidade dos preços dos concorrentes.

## Gold

A camada Gold possui uma tabela de scorecard de qualidade:

```text
gold.qualidade_dados
```

Essa tabela consolida regras e indicadores de qualidade para acompanhamento analítico.

Entre as verificações estão:

- vendas de produtos não cadastrados;
- vendas anteriores ao cadastro do produto;
- preços suspeitos de concorrentes;
- inconsistências de marca;
- nomes de produtos duplicados;
- produtos com poucos concorrentes;
- limpeza de nomes de clientes.

## Testes automatizados

Os testes automatizados estão localizados em:

```text
tests/testes_qualidade.py
```

Eles verificam aspectos como:

- estrutura das tabelas;
- presença de colunas;
- tipos de dados;
- chaves;
- valores nulos;
- valores positivos;
- regras de negócio;
- segmentação de clientes;
- consistência entre tabelas;
- métricas agregadas.

---

# Infrastructure as Code

O projeto utiliza Databricks Asset Bundles para versionar a infraestrutura do ambiente.

## Arquivo principal

```text
databricks.yml
```

## Recursos

```text
resources/
├── pipeline.yml
├── jobs.yml
├── dashboards.yml
└── genie.yml
```

### Recursos gerenciados

| Arquivo | Recurso |
|---|---|
| `pipeline.yml` | Lakeflow Pipeline |
| `jobs.yml` | Lakeflow Job |
| `dashboards.yml` | AI/BI Dashboard + SQL Warehouse |
| `genie.yml` | Genie Space + SQL Warehouse |

O Bundle utiliza:

```yaml
engine: direct
```

para permitir o gerenciamento dos recursos compatíveis com o mecanismo de implantação direta.

---

# Estrutura do Projeto

```text
Projeto_Ecommerce_Databricks/
│
├── README.md
├── .gitignore
├── .gitattributes
├── databricks.yml
│
├── data/
│       ├── clientes.csv
│       ├── produtos.csv
│       ├── vendas.csv
│       └── preco_competidores.csv
│
├── src/
│   ├── bronze/
│   │   ├── bronze_schema.sql
│   │   ├── ingest.py
│   │
│   ├── silver/
│   │   ├── clientes.py
│   │   ├── produtos.py
│   │   ├── preco_competidores.py
│   │   └── vendas.py
│   │
│   └── gold/
│       ├── clientes_segmentacao.sql
│       ├── vendas_temporais.sql
│       ├── vendas_produtos.sql
│       ├── vendas_detalhadas.sql
│       ├── precos_competitividade.sql
│       └── qualidade_dados.sql
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
│   ├── genie.md
│   ├── dashboard-demo.gif
│   ├── genie-demo.gif
│   └── TECHNICAL.md
│
└── resources/
    ├── pipeline.yml
    ├── jobs.yml
    ├── dashboards.yml
    └── genie.yml
```

---

# Governança

## Unity Catalog

O projeto utiliza o catálogo:

```text
projeto_dados
```

Com os schemas:

```text
bronze
silver
gold
```

O Unity Catalog organiza os objetos de dados e permite gerenciamento centralizado de metadados e permissões.

## Camadas de acesso

A separação das camadas permite diferenciar:

- dados brutos;
- dados tratados;
- dados preparados para consumo.

As tabelas Gold são o principal ponto de consumo para análises de negócio.

---

# Padrões de Código

## Convenções

- Nomes de tabelas e colunas em `snake_case`;
- Nomes sem acentos;
- Código organizado por camada;
- Regras de negócio documentadas;
- Transformações concentradas na Silver;
- Agregações e métricas analíticas concentradas na Gold;
- Catálogo parametrizado no Bundle;
- Regras de qualidade implementadas como Expectations ou testes.

## Silver

As transformações são implementadas em Python/PySpark.

Exemplo:

```python
from pyspark import pipelines as dp
from pyspark.sql import functions as F

@dp.materialized_view(
    comment="Descrição da tabela."
)
@dp.expect_all_or_fail({
    "campo_obrigatorio": "campo IS NOT NULL"
})
def tabela():
    return spark.read.table("bronze.tabela")
```

## Gold

As tabelas analíticas são implementadas utilizando Databricks SQL.

Exemplo:

```sql
CREATE OR REFRESH MATERIALIZED VIEW gold.tabela
COMMENT 'Descrição da tabela.'
AS
SELECT
    ...
FROM silver.origem;
```

---

# Observabilidade

A arquitetura utiliza diferentes mecanismos para acompanhar a qualidade e a execução do pipeline.

### Pipeline

- Event Log;
- Expectations;
- status das atualizações;
- erros de processamento.

### Jobs

- histórico de execução;
- status das execuções;
- duração;
- falhas.

### Testes

Os testes automatizados ajudam a detectar regressões nas tabelas e regras de negócio.

### Unity Catalog

A linhagem de dados pode ser utilizada para acompanhar dependências entre objetos e impactos de alterações.

---

# Tratamento de Problemas de Qualidade

O projeto adota como princípio que problemas de qualidade conhecidos devem ser identificados e, quando possível, preservados para análise.

Exemplo:

```text
Venda
  ↓
Produto não cadastrado?
  ↓
Sim
  ↓
Registro permanece na Silver
  ↓
Flag: produto_cadastrado = false
```

Essa abordagem evita eliminar informações potencialmente relevantes sem uma regra de negócio explícita.

---

# Estratégias de Performance

O projeto utiliza recursos do Databricks voltados à eficiência de processamento e consulta:

- Serverless Compute;
- Materialized Views;
- Delta Lake;
- agregações pré-computadas na Gold;
- redução de transformações repetidas no consumo analítico.

O uso de estratégias adicionais de otimização deve considerar o volume de dados e o padrão real de consultas antes de serem aplicadas.

---

# Próximos Passos

As seguintes evoluções podem ser consideradas futuramente:

- [ ] Processamento incremental;
- [ ] CDC (Change Data Capture);
- [ ] Streaming Tables quando houver necessidade de processamento contínuo;
- [ ] Monitoramento automatizado de qualidade;
- [ ] Alertas para regras críticas;
- [ ] CI/CD com GitHub Actions;
- [ ] Expansão das tabelas Gold;
- [ ] Análises de cohort;
- [ ] Segmentação RFM;
- [ ] Estratégias adicionais de otimização conforme o crescimento dos dados;
- [ ] Modelos preditivos para casos de uso de negócio.

---

# Referências

- [Databricks Lakehouse Architecture](https://www.databricks.com/product/data-lakehouse)
- [Delta Lake](https://delta.io/)
- [Unity Catalog](https://docs.databricks.com/en/data-governance/unity-catalog/)
- [Lakeflow](https://docs.databricks.com/en/delta-live-tables/)
- [Databricks Asset Bundles](https://docs.databricks.com/en/dev-tools/bundles/)
- [Genie Spaces](https://docs.databricks.com/en/genie/)

---

# Decisões de Arquitetura

## Por que utilizar Medallion Architecture?

A separação em Bronze, Silver e Gold permite:

- separar ingestão e transformação;
- facilitar a rastreabilidade;
- organizar responsabilidades;
- reutilizar dados tratados em diferentes casos de uso;
- disponibilizar dados específicos para consumo analítico.

## Por que utilizar Materialized Views?

As Materialized Views são utilizadas nas transformações do projeto porque as tabelas são derivadas de dados já disponíveis e precisam estar preparadas para consumo analítico.

Isso permite:

- centralizar as transformações;
- manter as dependências entre tabelas;
- disponibilizar dados pré-processados para consultas.

## Por que separar Silver e Gold?

A Silver concentra limpeza, padronização, enriquecimento e qualidade.

A Gold concentra regras de negócio, agregações e estruturas voltadas diretamente ao consumo.

Essa separação evita misturar tratamento técnico dos dados com lógica analítica.

## Por que marcar problemas em vez de descartar?

Nem todo problema de qualidade significa que o registro deve ser eliminado.

Ao utilizar flags, é possível:

- medir a ocorrência do problema;
- preservar o registro original tratado;
- manter a rastreabilidade;
- permitir que a camada Gold decida como utilizar a informação.

---

> **Nota:** Esta documentação descreve a arquitetura implementada no projeto e seus principais componentes. Configurações específicas de produção, como catálogos separados, permissões, identidades de execução e CI/CD, podem exigir adaptações conforme o ambiente de implantação.