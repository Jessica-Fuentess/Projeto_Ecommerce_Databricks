# 🎯 PROMPT AGENTES IA — DIRETORIA

## A AGENTE DO GENIE PARA OS DIRETORES

Agora os diretores vão perguntar sozinhos, em português. Crie um Genie Space chamado **"Diretoria E-commerce 2026"**, como código dentro deste bundle, em cima da Gold. Use o catálogo `projeto_dados` e o warehouse **"Serverless Starter Warehouse"**.

### CONTEXTO

- O Genie não sabe nada da empresa: tudo o que ele sabe vem das tabelas, dos comentários das colunas e do que colocarmos no Space. Os comentários da Gold já existem; leia antes de escrever qualquer instrução e não repita nas instruções o que o comentário já diz.
- Um único Space atende os três diretores: **Comercial** (vendas), **Customer Success** (clientes) e **Pricing** (preços da concorrência: Mercado Livre, Amazon, Magalu e Shopee).

### CONVENÇÕES

- O Space fica em `genie/diretoria_ecommerce.geniespace.json` (o serialized Space exportado) e o recurso em `resources/diretoria.genie_space.yml`, com o warehouse por lookup do nome e `parent_path: /Workspace/Users/${workspace.current_user.userName}`.
- Mudou uma instrução? Edite o JSON via SDK e faça deploy. Nada de ajustar o Space pela interface, que se perde no próximo deploy (etag conflict no bundle).
- Os identificadores das tabelas ficam escritos no JSON (`projeto_dados.gold.*`), porque o arquivo não passa por variáveis do bundle.
- O `space_id` muda entre dev e prod: anote nas instruções do projeto.

---

## O QUE VAI NO SPACE

### Tabelas

As **5 Golds**:

- `projeto_dados.gold.vendas_temporais`
- `projeto_dados.gold.vendas_produtos`
- `projeto_dados.gold.vendas_detalhadas`
- `projeto_dados.gold.clientes_segmentacao`
- `projeto_dados.gold.precos_competitividade`

**Nenhuma tabela da Bronze ou da Silver.**

### Instruções gerais

Curtas (até aproximadamente 2.500 caracteres), somente com regras de negócio que não estejam suficientemente cobertas pelos comentários:

- Responder em **português**.
- Dinheiro em **R$ com 2 casas decimais**.
- **Receita é bruta** e não existem dados de custo, margem ou lucro.
- O **período vai de 13/12/2025 a 11/01/2026**. Expressões como "no mês" ou "até agora" devem considerar o período completo do projeto. Nunca usar `current_date()` para alterar esse período.
- "Hoje", "ontem" e "esta semana" não devem ser respondidos como se existissem dados atuais. Explique que os dados terminam em 11/01/2026 e pergunte se o usuário quer analisar 11/01/2026 ou outro período existente.
- **Qual tabela usar** para cada tipo de pergunta:
  - tempo e canal → `vendas_temporais`;
  - produto → `vendas_produtos`;
  - cliente → `clientes_segmentacao`;
  - preço → `precos_competitividade`;
  - perguntas que cruzam diretorias ou precisam do nível individual da venda → `vendas_detalhadas`.
- **Ticket médio** = receita ÷ número de vendas:
  - `SUM(total_vendas)` em `vendas_temporais` e `vendas_produtos`;
  - `COUNT(*)` em `vendas_detalhadas`;
  - `SUM(total_compras)` em `clientes_segmentacao`.
- Contar produto por **`id_produto`**.
- **Dia da semana:** usar receita média por ocorrência do dia no período, citando também o dia de maior receita total e explicando a diferença quando necessário.
- **Segmentos:** VIP (≥ R$ 22.000), TOP_TIER (R$ 17.000 a R$ 21.999,99), REGULAR (< R$ 17.000).
- "Mais caro que o mercado" = `diferenca_pct_vs_media > 0`.
- "Mais caro que todos" = `classificacao_preco = 'MAIS_CARO_QUE_TODOS'`.
- Toda contagem de produtos em `precos_competitividade` deve separar os confirmados dos que têm preço suspeito (a confirmar antes de reagir), informar o total e as categorias dos suspeitos.
- Em "qual X vende mais", trazer receita, número de vendas e ticket médio. Informar número de clientes (`COUNT(DISTINCT id_cliente)`) somente em perguntas por região, estado ou segmento. Nunca somar `clientes_unicos`.
- Canais exibidos como **"E-commerce"** e **"Loja física"**.
- **Rankings com 10 linhas**, salvo quando o usuário solicitar explicitamente outra quantidade.

### Joins

- `vendas_produtos × precos_competitividade` por `id_produto` (um para um).
- `vendas_detalhadas × clientes_segmentacao` por `id_cliente` (muitos para um).
- Quando necessário para resultados determinísticos na API, ordenar por identificador (`ORDER BY id_produto` ou `ORDER BY id_cliente`) após aplicar a ordenação principal da pergunta. Não deixar uma ordenação auxiliar substituir o critério solicitado pelo usuário.

### SQL de exemplo

Pergunta → SQL certo para as contas em que a IA costuma errar, **SEM repetir as perguntas do teste abaixo** (senão o teste vira cola):

1. Ticket médio por segmento de cliente.
2. Participação dos TOP_TIER na receita.
3. Receita por região e categoria usando `vendas_detalhadas`.
4. Quantos produtos estão mais caros que a média do mercado, numa contagem com uma linha por situação (confirmado ou a confirmar), o total e as categorias dos suspeitos.
5. Ticket médio usando `vendas_temporais`.

Regra que falha em texto costuma passar com um SQL de exemplo no formato correto.

**Teste cada SQL no warehouse.**

### Sinônimos nas colunas

- faturamento → `receita`
- UF → `estado`
- canal → `canal_venda`
- perfil → `segmento_cliente`
- posição de preço → `classificacao_preco`

### Perguntas iniciais

Configure **6 perguntas de exemplo** na tela inicial, duas de cada diretoria, e teste todas. Nenhuma pode retornar vazia ou erro.

---

## TESTE

Faça o deploy em dev e pergunte ao Space pela **API de conversa do Genie**.

Para cada pergunta:

1. faça a pergunta ao Genie;
2. execute um SQL independente diretamente nas Golds para obter o esperado;
3. compare a resposta;
4. registre em uma tabela:

| Pergunta | Resposta do Genie | Esperado | Acertou? |
|---|---|---|---|

Só conta como acerto se a resposta trouxer **todos os números do esperado** e os nomes/entidades relevantes estiverem corretos.

### 10 Perguntas Principais

1. **Qual foi a receita total do período?**  
   → R$ 974.077,28

2. **Qual canal vende mais?**  
   → E-commerce: 2.155 vendas, R$ 705.486,21, ticket R$ 327,37

3. **Quais os 5 produtos que mais faturaram?**  
   → Fone de Ouvido Esportivo, Camisa Social, Necessaire, Persiana Vertical e Calça Jeans Skinny

4. **Qual categoria gerou mais receita?**  
   → Moda, R$ 248.124,15

5. **Quem são os 5 melhores clientes?**  
   → Ana Sophia Pereira (MG, R$ 30.716,63) em primeiro

6. **Quantos clientes VIP temos e quanto representam da receita?**  
   → 10, R$ 262.806,22, 27,0%

7. **Qual região gera mais receita?**  
   → Norte, R$ 333.078,69, 17 clientes

8. **Qual dia da semana vende mais?**  
   → quarta-feira pela média por dia (R$ 34.753,61); sábado somente pelo total, porque ocorreu 5 vezes no período

9. **Quantos produtos estão mais caros que todos os concorrentes?**  
   → 35: 20 confirmados e 15 com preço suspeito a confirmar, todos de Tênis

10. **Dos 10 produtos que mais faturam, quais estão mais caros que a média do mercado?**  
    → 5: Camisa Social, Persiana Vertical, Shorts Jeans, Vestido Floral e Notebook Inspiron 15

### 2 Perguntas de Limite

O Genie deve responder sem inventar:

- **"Qual foi o nosso lucro?"**
  - Explicar que não existem dados de custo, margem ou lucro.

- **"Quanto vendemos ontem?"**
  - Explicar que os dados terminam em 11/01/2026 e não utilizar `current_date()`.

### Iteração

Se errar, **não mude o esperado**.

Melhore somente o que for necessário no contexto do Space:

- comentário;
- instrução;
- join;
- SQL de exemplo;
- configuração da tabela.

Depois faça o deploy e pergunte novamente.

Registre o placar de cada rodada e o que mudou entre elas.

Exemplo:

| Rodada | Perguntas corretas | Problema | Alteração |
|---|---:|---|---|
| 1 | 10/12 | ... | ... |
| 2 | 12/12 | ... | ... |

Essa etapa deve servir também para documentar o aprendizado sobre o comportamento do Genie.

---

## NO FIM

Ligue o botão **"Ask Genie"** dos 3 dashboards a este Space.

O `space_id` fica fixo no JSON do dashboard em cada ambiente. Registre nas instruções do projeto que o `space_id` de produção é diferente do ambiente dev.

Faça o deploy final.

Apresente:

- nome do Space;
- catálogo utilizado;
- 5 tabelas Gold utilizadas;
- instruções configuradas;
- joins configurados;
- SQLs de exemplo configurados;
- 6 perguntas iniciais;
- resultado das 10 perguntas principais;
- resultado das 2 perguntas de limite;
- número de rodadas;
- alterações realizadas entre as rodadas;
- integração dos 3 dashboards com "Ask Genie";
- link do Space.

---

# RESULTADO OBTIDO

> **Preencher/atualizar esta seção após a execução final.**

- **Space criado:** Diretoria E-commerce 2026
- **ID (dev):** `01f1baca9ba71b49a15315cbadc3b588`
- **Catálogo:** `projeto_dados`
- **Tabelas:** 5 Gold
- **Testes:** 12/12 (10 principais + 2 limites)
- **Iterações:** 2 rodadas

### Rodadas

- **Rodada 1:** Pergunta 8 (dia da semana) retornava total em vez de média → reforçada a instrução para ordenar pela média.
- **Rodada 2:** Pergunta 9 (preços suspeitos) não separava confirmados → corrigida a instrução para reportar total + categorias suspeitas.

### Dashboard

- Integrado com **Ask Genie** funcional.

### Link

`https://dbc-b7666745-6272.cloud.databricks.com/genie/spaces/01f1baca9ba71b49a15315cbadc3b588`
