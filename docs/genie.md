# Genie — Diretoria E-commerce

## Objetivo

O Genie disponibiliza uma camada de análise em linguagem natural sobre as
tabelas Gold do projeto, permitindo consultas em português sobre vendas,
clientes e competitividade de preços.

O Space utiliza exclusivamente dados da camada Gold do catálogo
`projeto_dados`.

## Fontes de dados

O Space foi estruturado para utilizar cinco tabelas:

| Tabela | Finalidade |
|---|---|
| `projeto_dados.gold.vendas_temporais` | Análises por data, hora e canal |
| `projeto_dados.gold.vendas_produtos` | Análises e rankings por produto |
| `projeto_dados.gold.vendas_detalhadas` | Análises no nível individual da venda |
| `projeto_dados.gold.clientes_segmentacao` | Segmentação, receita e ranking de clientes |
| `projeto_dados.gold.precos_competitividade` | Comparação de preços com concorrentes |

## Áreas de negócio

### Comercial

Perguntas relacionadas a:

- receita;
- quantidade de vendas;
- canais de venda;
- produtos;
- categorias;
- períodos;
- rankings.

### Customer Success

Perguntas relacionadas a:

- clientes;
- receita por cliente;
- segmentos;
- ranking;
- estado e região;
- ticket médio.

### Pricing

Perguntas relacionadas a:

- preço próprio;
- preço dos concorrentes;
- diferença percentual;
- classificação de preço;
- produtos mais caros ou mais baratos que o mercado.

## Regras de interpretação

### Período

O conjunto de dados utilizado neste projeto cobre:

**13/12/2025 a 11/01/2026**

Perguntas com referências como "hoje" ou "ontem" não devem ser interpretadas
como datas posteriores ao período disponível.

### Receita

`receita` representa o valor das vendas.

O modelo não possui dados suficientes para calcular:

- custo;
- margem;
- lucro;
- resultado financeiro.

Essas métricas não devem ser inferidas pelo Genie.

### Segmentação de clientes

A classificação utilizada na Gold é:

| Segmento | Regra |
|---|---|
| VIP | Receita >= R$ 22.000 |
| TOP_TIER | Receita >= R$ 17.000 e < R$ 22.000 |
| REGULAR | Receita < R$ 17.000 |

### Pricing

Para identificar produtos mais caros que todos os concorrentes, utilizar:

`classificacao_preco = 'MAIS_CARO_QUE_TODOS'`

Para analisar a diferença percentual em relação à média dos concorrentes,
utilizar:

`diferenca_pct_vs_media`

## Seleção da tabela

O Genie deve priorizar a tabela mais adequada à pergunta:

- **Tempo / hora / canal:** `vendas_temporais`
- **Produto:** `vendas_produtos`
- **Cliente / segmento / ranking:** `clientes_segmentacao`
- **Preço / concorrência:** `precos_competitividade`
- **Venda individual ou cruzamentos detalhados:** `vendas_detalhadas`

## Relacionamentos relevantes

### Vendas × Clientes

```text
vendas_detalhadas.id_cliente
        =
clientes_segmentacao.id_cliente
```

Relacionamento: muitas vendas para um cliente.

### Produtos × Pricing

```text
vendas_produtos.id_produto
        =
precos_competitividade.id_produto
```

Relacionamento: um registro agregado por produto em cada tabela.

## Exemplos de perguntas

- Qual foi a receita total do período?
- Quais são os 10 produtos com maior receita?
- Quantos clientes são VIP?
- Qual região concentra a maior receita?
- Quantos produtos estão mais caros que todos os concorrentes?
- Qual é a diferença média de preço em relação aos concorrentes?

## Validação

Antes de considerar o Space pronto para uso, as perguntas de negócio devem
ser comparadas com consultas SQL independentes executadas diretamente nas
tabelas Gold.

A validação deve verificar:

1. se o Genie selecionou a tabela adequada;
2. se aplicou corretamente os filtros;
3. se utilizou a métrica correta;
4. se os valores retornados correspondem às consultas SQL de referência.

Os resultados dessa validação devem ser atualizados quando as tabelas Gold
ou as regras de negócio forem alteradas.

## Versionamento

A documentação deste arquivo (`genie.md`) descreve o objetivo, as fontes,
as regras e a estratégia de validação sem expor o prompt completo utilizado
durante a configuração.
