# PROMPT 3 — GOLD COMERCIAL

## ANTES DE COMEÇAR

1. Leia `PROJECT_RULES.md`.
2. Leia e verifique as Golds e Silver existentes.
3. Trabalhe exclusivamente no catálogo `projeto_dados`.
4. Use o perfil Databricks CLI `imersao`.
5. Não exponha nem grave tokens ou credenciais.

Nesta etapa implemente somente a Gold da Diretoria Comercial.

## REGRAS

Use SQL.

Um arquivo por tabela em:

`transformations/gold/`

Todas as tabelas devem ser:

```sql
CREATE OR REFRESH MATERIALIZED VIEW
```

Declare todas as colunas com nome, tipo e `COMMENT`.

Declare `COMMENT` na tabela.

Comentários em português.

Inclua no comentário das tabelas o período:

**13/12/2025 a 11/01/2026.**

Inclua todas as vendas, inclusive produtos não cadastrados.

Receita representa dinheiro que entrou.

---

# TABELA 1 — `gold.vendas_temporais`

Uma linha por:

`data × hora × canal_venda`.

## Colunas

- `data`;
- `dia_semana`;
- `dia_semana_num`;
- `hora`;
- `canal_venda`;
- `total_vendas`;
- `itens_vendidos`;
- `receita`;
- `clientes_unicos`.

## Regras

- `total_vendas = COUNT`;
- `itens_vendidos = SUM(quantidade)`;
- `receita = SUM(receita)`;
- `clientes_unicos = COUNT DISTINCT id_cliente`.

No `COMMENT` de `clientes_unicos`, explique:

> "Não somar entre linhas. Para clientes únicos no período completo, utilizar gold.clientes_segmentacao."

---

# TABELA 2 — `gold.vendas_produtos`

Uma linha por produto vendido.

Usar `LEFT JOIN` de `silver.vendas` com `silver.produtos`.

## Colunas

- `id_produto`;
- `nome_produto`;
- `categoria`;
- `marca`;
- `faixa_preco`;
- `produto_cadastrado`;
- `total_vendas`;
- `itens_vendidos`;
- `receita`;
- `ticket_medio`;
- `ranking_receita`;
- `ranking_na_categoria`.

Quando o produto não existir:

```text
nome_produto = "Produto não cadastrado"
categoria = "Não cadastrado"
marca = "Não cadastrado"
```

## Regras

- `total_vendas = COUNT`;
- `itens_vendidos = SUM(quantidade)`;
- `receita = SUM(receita)`;
- `ticket_medio = ROUND(AVG(receita), 2)`;
- `ranking_receita = ROW_NUMBER()` geral por `receita DESC`;
- `ranking_na_categoria = ROW_NUMBER()` particionado por `categoria` e ordenado por `receita DESC`.

No `COMMENT` de `nome_produto`, explique que produtos diferentes podem possuir o mesmo nome e que análises de produto devem utilizar `id_produto`.

---

# TABELA 3 — `gold.vendas_detalhadas`

Uma linha por venda.

Essa tabela será utilizada para perguntas que cruzam diretorias e filtros cruzados do dashboard.

## Colunas

- `id_venda`;
- `data_venda`;
- `data`;
- `dia_semana`;
- `dia_semana_num`;
- `hora`;
- `canal_venda`;
- `id_produto`;
- `nome_produto`;
- `categoria`;
- `marca`;
- `faixa_preco`;
- `produto_cadastrado`;
- `id_cliente`;
- `nome_cliente`;
- `estado`;
- `regiao`;
- `segmento_cliente`;
- `quantidade`;
- `preco_unitario`;
- `receita`;
- `venda_antes_do_cadastro`.

Utilize os mesmos valores `"Produto não cadastrado"` e `"Não cadastrado"` definidos em `vendas_produtos`.

Obtenha `segmento_cliente` a partir de `gold.clientes_segmentacao`.

Utilize:

```sql
CLUSTER BY (data)
```

---

# TESTES

Adicionar ao notebook:

`testes/testes_qualidade.py`

Testes obrigatórios:

- receita total de `vendas_temporais` igual à de `silver.vendas`;
- receita total de `vendas_produtos` igual à de `silver.vendas`;
- receita total de `vendas_detalhadas` igual à de `silver.vendas`;
- `vendas_detalhadas` com o mesmo número de linhas de `silver.vendas`;
- `id_venda` único em `vendas_detalhadas`;
- toda venda de `vendas_detalhadas` deve possuir `segmento_cliente` e `regiao`.

---

# VALIDAÇÃO

Execute:

```bash
databricks bundle validate --strict
```

Depois faça deploy em dev, execute o Job e acompanhe até terminar.

Confira:

- receita R$ 974.077,28;
- 3.020 vendas em `silver.vendas`;
- 3.020 vendas em `vendas_temporais`;
- 3.020 vendas em `vendas_produtos`;
- 3.020 vendas em `vendas_detalhadas`;
- 2.155 vendas no ecommerce.

**Não force os números. Se houver diferença, investigue e explique.**
