# PROMPT 2 — GOLD CUSTOMER SUCCESS

## ANTES DE COMEÇAR

1. Leia `PROJECT_RULES.md`.
2. Verifique as tabelas Silver criadas no Prompt 1.
3. Não altere a Bronze.
4. Trabalhe exclusivamente no catálogo `projeto_dados`.
5. Use o perfil Databricks CLI `imersao`.
6. Não exponha nem grave tokens ou credenciais.

Nesta etapa implemente somente a Gold de Customer Success.

## REGRAS PARA TODA GOLD

- SQL;
- um arquivo por tabela em `transformations/gold/`;
- usar `CREATE OR REFRESH MATERIALIZED VIEW`;
- schema `gold`;
- declarar todas as colunas com nome, tipo e `COMMENT`;
- declarar `COMMENT` na tabela;
- comentários em português;
- comentários devem informar regra de cálculo, unidade quando aplicável e avisos que evitem interpretações incorretas pelo Genie;
- período dos dados: 13/12/2025 a 11/01/2026;
- incluir todas as vendas, inclusive vendas de produtos não cadastrados;
- receita representa dinheiro que entrou;
- adicionar os testes da Gold ao notebook `testes/testes_qualidade.py`.

## TABELA

### `gold.clientes_segmentacao`

Uma linha por cliente.

Comece por `silver.clientes` e utilize `LEFT JOIN` com as vendas para manter inclusive clientes que nunca compraram.

### Colunas

- `id_cliente`;
- `nome_cliente`;
- `estado`;
- `nome_estado`;
- `regiao`;
- `total_compras`;
- `receita`;
- `ticket_medio`;
- `primeira_compra`;
- `ultima_compra`;
- `segmento_cliente`;
- `ranking_receita`.

### Regras

- `receita` = soma da receita das vendas;
- cliente sem compra deve ter `receita = 0`;
- `total_compras` = quantidade de vendas;
- `ticket_medio` = `ROUND(AVG(receita), 2)` considerando as vendas do cliente;
- `primeira_compra` = menor data de venda;
- `ultima_compra` = maior data de venda;
- `ranking_receita` = `ROW_NUMBER()` ordenado por `receita DESC`.

## SEGMENTAÇÃO

### VIP

```text
receita >= 22000
```

### TOP_TIER

```text
receita >= 17000
e
receita < 22000
```

### REGULAR

```text
receita < 17000
```

Explique no comentário do arquivo por que os limites antigos de R$ 10.000 e R$ 5.000 não são utilizados: com eles quase todos os clientes seriam classificados como VIP.

## TESTES

Adicionar ao notebook:

- receita total de `gold.clientes_segmentacao` igual à receita de `silver.vendas`;
- `id_cliente` único;
- `segmento_cliente` somente `VIP`, `TOP_TIER` ou `REGULAR`;
- nenhum VIP com receita abaixo de 22000;
- todas as colunas da Gold devem possuir `COMMENT`;
- ignorar objetos internos cujo nome comece com `__materialization`.

## VALIDAÇÃO

Execute:

```bash
databricks bundle validate --strict
```

Depois faça deploy em dev, execute o Job e acompanhe até terminar.

Confira:

- 50 clientes;
- 10 VIP;
- 25 TOP_TIER;
- 15 REGULAR;
- receita R$ 974.077,28;
- maior cliente: Ana Sophia Pereira, MG, R$ 30.716,63.

**Não altere os dados para fazer os números baterem. Se houver diferença, investigue e explique.**
