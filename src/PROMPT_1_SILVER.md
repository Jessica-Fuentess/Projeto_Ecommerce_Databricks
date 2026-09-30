# PROMPT 1 — SILVER

Use o perfil de autenticação Databricks CLI
"imersao" em todas as operações.

Nunca exponha, imprima, grave ou hardcode
tokens ou outras credenciais.

## IMPORTANTE

Trabalhe exclusivamente no catálogo
`projeto_dados`.

Não use outro catálogo.

## FASE 1 — EXPLORAÇÃO DA BRONZE

Antes de escrever ou alterar qualquer código,
explore as quatro tabelas Bronze:

- `projeto_dados.bronze.vendas`
- `projeto_dados.bronze.produtos`
- `projeto_dados.bronze.clientes`
- `projeto_dados.bronze.preco_competidores`

Mostre:

- quantidade de registros;
- colunas e tipos;
- valores nulos;
- duplicidades;
- vendas de produtos não cadastrados;
- vendas anteriores à criação do produto;
- preços de concorrentes fora do padrão;
- clientes com pronome de tratamento no início do nome.

Não altere nenhum dado da Bronze.

Compare os resultados encontrados com os números esperados no final deste prompt.

**IMPORTANTE:**

Se os números forem diferentes dos esperados,
**NÃO altere as regras para forçar os resultados.**

Mostre a diferença e investigue a causa.

Somente depois de concluir a exploração e
apresentar os resultados, prossiga para a implementação.

## FASE 2 — REGRAS DO PROJETO

Crie o arquivo `PROJECT_RULES.md` na raiz do
bundle com as regras gerais que deverão ser utilizadas nos próximos prompts.

O arquivo deve registrar:

- catálogo: `projeto_dados`;
- schemas: `bronze`, `silver` e `gold`;
- nomes de tabelas e colunas em português,
  `snake_case` e sem acentos;
- Silver em Python usando `from pyspark import pipelines as dp`;
- Gold em SQL;
- um arquivo por tabela;
- Silver em `transformations/silver/`;
- Gold em `transformations/gold/`;
- materialized views com leitura batch;
- não utilizar streaming tables para a Silver, pois a Bronze é sobrescrita a cada execução;
- pipeline serverless;
- catálogo do pipeline: `projeto_dados`;
- schema padrão do pipeline: `silver`;
- dinheiro sempre como `DECIMAL(10,2)`;
- problemas conhecidos de qualidade devem ser marcados e medidos com expectations em modo warn;
- nunca descartar linhas por problemas de qualidade conhecidos;
- usar fail somente para regras que nunca podem acontecer;
- validar sempre com `databricks bundle validate --strict` antes do deploy;
- comentários em português explicando o **PORQUÊ** das regras de negócio.

Não crie um `CLAUDE.md`. Use `PROJECT_RULES.md`
como documento de regras deste projeto.

## FASE 3 — IMPLEMENTAÇÃO DA SILVER

Crie as quatro tabelas Silver como
materialized views usando Python e leitura batch.

Arquivos:

- `transformations/silver/produtos.py`
- `transformations/silver/clientes.py`
- `transformations/silver/preco_competidores.py`
- `transformations/silver/vendas.py`

Remova os exemplos que vieram no template.

Cada arquivo deve começar com comentários em
português explicando o **PORQUÊ** das principais regras de negócio.

### SILVER.PRODUTOS

Chave: `id_produto`.

Regras:

- remover duplicidades por `id_produto`;
- `trim` em `nome_produto`;
- `preco_atual` como `DECIMAL(10,2)`;
- criar `faixa_preco`:
  - `PREMIUM` quando `preco_atual > 1000`;
  - `MEDIO` quando `preco_atual > 500`;
  - `BASICO` nos demais casos.

Regras que devem falhar:

- `id_produto` preenchido;
- `preco_atual > 0`.

### SILVER.CLIENTES

Chave: `id_cliente`.

Regras:

- remover duplicidades por `id_cliente`;
- preservar o nome original em `nome_original`;
- remover do início de `nome_cliente` os pronomes `Sr.`, `Sra.`, `Srta.`, `Dr.` e `Dra.`;
- `nome_cliente` em formato título;
- `estado` em letras maiúsculas;
- criar `nome_estado`;
- criar `regiao`.

Use um mapeamento fixo das 27 UFs do IBGE
declarado no próprio arquivo.

Regiões:

- Norte;
- Nordeste;
- Centro-Oeste;
- Sudeste;
- Sul.

Não existe tabela de estados na Bronze.

Regras que devem falhar:

- `id_cliente` preenchido;
- `regiao` preenchida.

### SILVER.PRECO_COMPETIDORES

Chave composta:

`id_produto + nome_concorrente`.

Regras:

- remover duplicidades pela chave composta;
- `preco_concorrente` como `DECIMAL(10,2)`;
- converter `data_coleta` de texto para `timestamp`;
- criar `preco_suspeito = true` quando `preco_concorrente < 60% do preco_atual do produto`;
- criar `preco_plausivel = NOT preco_suspeito`.

Regras que devem falhar:

- `id_produto` preenchido;
- `preco_concorrente > 0`.

Regras em modo warn:

- `preco_plausivel`.

### SILVER.VENDAS

Chave: `id_venda`.

Regras:

- remover duplicidades por `id_venda`;
- `preco_unitario` como `DECIMAL(10,2)`;
- `receita = quantidade × preco_unitario` como `DECIMAL(10,2)`;
- criar `data` como `date`;
- criar `hora` no intervalo 0-23;
- criar `dia_semana_num`:
  - 1 = Domingo
  - 2 = Segunda
  - 3 = Terça
  - 4 = Quarta
  - 5 = Quinta
  - 6 = Sexta
  - 7 = Sábado;
- criar `dia_semana` em português.

Criar `produto_cadastrado`:

- `true` quando `id_produto` existir em `silver.produtos`;
- `false` quando não existir.

Criar `venda_antes_do_cadastro`:

- `true` somente quando o produto existir e `data_venda` for anterior à `data_criacao`;
- `false` caso contrário.

Criar `venda_depois_do_cadastro`:

- `true` somente quando o produto estiver cadastrado e `data_venda >= data_criacao`;
- `false` caso contrário.

Regras que devem falhar:

- `id_venda` preenchido;
- `data_venda` preenchida;
- `id_cliente` preenchido;
- `id_produto` preenchido;
- `quantidade` preenchida;
- `preco_unitario` preenchido;
- `quantidade > 0`;
- `preco_unitario > 0`;
- `canal_venda` em (`'ecommerce'`, `'loja_fisica'`).

Regras em modo warn:

- `produto_cadastrado`;
- `venda_depois_do_cadastro`.

## TESTES DE QUALIDADE

Crie:

`testes/testes_qualidade.py`

O notebook deve estar no formato source do
Databricks e possuir um widget `catalogo` com valor padrão
`projeto_dados`.

Cada teste deve contar as linhas com
problema.

Se algum teste encontrar problema, o notebook
deve falhar com `AssertionError` e mostrar uma tabela consolidada com o resultado
dos testes.

Testes obrigatórios:

1. Chaves únicas das quatro tabelas Silver.
2. Receita = quantidade × preco_unitario.
3. Vendas de produto não cadastrado abaixo de 1% do total.

## PIPELINE E JOB

Configure o pipeline Lakeflow Declarative
Pipeline existente no bundle, utilizando:

- pipeline serverless;
- catálogo `projeto_dados`;
- schema padrão `silver`.

Não utilize streaming tables.

Crie ou atualize o Job `Pipeline E-commerce` para:

1. executar o pipeline;
2. depois executar o notebook `testes/testes_qualidade.py`.

## VALIDAÇÃO

Antes do deploy:

```bash
databricks bundle validate --strict
```

Depois:

1. faça o deploy em dev;
2. execute o Job;
3. acompanhe até terminar;
4. se houver falha, leia o erro e corrija;
5. mostre as métricas das expectations no event log do pipeline.

## NÚMEROS ESPERADOS

- 3.020 vendas;
- receita total R$ 974.077,28;
- 20 vendas de produto não cadastrado;
- receita dessas vendas R$ 4.240,01;
- 5 vendas antes do cadastro;
- receita dessas vendas R$ 325,88;
- 55 preços de concorrente suspeitos;
- 11 clientes com pronome de tratamento.

Clientes por região:

- Norte: 17;
- Nordeste: 12;
- Centro-Oeste: 9;
- Sudeste: 8;
- Sul: 4.

Se qualquer resultado for diferente, não
force o resultado. Investigue e explique a diferença.
