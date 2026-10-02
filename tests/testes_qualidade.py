"""
Testes de Qualidade - Projeto Dados Lakehouse
==============================================

Script para validação automatizada da qualidade dos dados nas tabelas Gold.
Testa integridade, completude, consistência e valores esperados.

"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, sum as sql_sum, round as sql_round, abs as sql_abs
from datetime import datetime
from typing import List
import argparse

# ========================================
# CONFIGURAÇÃO
# ========================================

CATALOG = "projeto_dados"
SCHEMA_GOLD = "gold"

# Valores esperados (baseline do período 13/12/2025 a 11/01/2026)
EXPECTED_VALUES = {
    "receita_total": 974077.28,
    "total_vendas": 3020,
    "total_clientes": 50,
    "clientes_vip": 10,
    "receita_vip": 262806.22,
    "produtos_monitorados": 215,
    "produtos_mais_caros_todos": 35,
    "total_linhas_vendas_temporais": 908
}

# Tolerância para comparações numéricas (0.01 = 1%)
TOLERANCE = 0.01

# ========================================
# CLASSE DE TESTES
# ========================================

class TestesQualidadeDados:
    """Bateria de testes de qualidade para as tabelas Gold."""

    def __init__(self, spark: SparkSession, catalog: str):
        self.spark = spark
        self.catalog = catalog
        self.resultados = []
        self.total_testes = 0
        self.testes_passaram = 0

    def registrar_resultado(self, nome_teste: str, passou: bool, mensagem: str = ""):
        """Registra resultado de um teste."""
        self.total_testes += 1
        if passou:
            self.testes_passaram += 1
            status = "✅ PASS"
        else:
            status = "❌ FAIL"

        self.resultados.append({
            "teste": nome_teste,
            "status": status,
            "passou": passou,
            "mensagem": mensagem
        })

        print(f"{status} | {nome_teste}")
        if mensagem:
            print(f"       {mensagem}")

    def assert_equal(self, nome: str, obtido, esperado, mensagem: str = ""):
        """Compara valor obtido com esperado."""
        passou = obtido == esperado
        msg = mensagem or f"Obtido: {obtido}, Esperado: {esperado}"
        self.registrar_resultado(nome, passou, msg)
        return passou

    def assert_close(self, nome: str, obtido: float, esperado: float, mensagem: str = ""):
        """Compara valores numéricos com tolerância."""
        if esperado == 0:
            passou = abs(obtido) < TOLERANCE
        else:
            passou = abs((obtido - esperado) / esperado) < TOLERANCE

        msg = mensagem or f"Obtido: R$ {obtido:,.2f}, Esperado: R$ {esperado:,.2f}"
        self.registrar_resultado(nome, passou, msg)
        return passou

    def assert_not_null(self, nome: str, df, colunas: List[str]):
        """Valida que colunas não têm valores nulos."""
        for coluna in colunas:
            nulos = df.filter(col(coluna).isNull()).count()
            passou = nulos == 0
            msg = f"Coluna '{coluna}': {nulos} nulos encontrados"
            self.registrar_resultado(f"{nome} - {coluna}", passou, msg)

    def assert_positive(self, nome: str, df, colunas: List[str]):
        """Valida que colunas numéricas são positivas."""
        for coluna in colunas:
            invalidos = df.filter(col(coluna) <= 0).count()
            passou = invalidos == 0
            msg = f"Coluna '{coluna}': {invalidos} valores inválidos (<= 0)"
            self.registrar_resultado(f"{nome} - {coluna}", passou, msg)

    def assert_schema(
        self,
        nome: str,
        df,
        colunas_esperadas: dict[str, str]
    ):
        """Valida nomes e tipos das colunas."""

        colunas_atuais = {
            campo.name: campo.dataType.simpleString()
            for campo in df.schema.fields
        }

        # Verifica presença das colunas
        colunas_faltantes = sorted(
            set(colunas_esperadas) - set(colunas_atuais)
        )

        self.assert_equal(
            f"{nome}: colunas obrigatórias",
            colunas_faltantes,
            [],
            f"Colunas faltantes: {colunas_faltantes}"
        )

        # Verifica tipos
        tipos_invalidos = {}

        for coluna, tipo_esperado in colunas_esperadas.items():
            tipo_atual = colunas_atuais.get(coluna)

            if tipo_atual != tipo_esperado:
                tipos_invalidos[coluna] = {
                    "esperado": tipo_esperado,
                    "obtido": tipo_atual,
                }

        self.assert_equal(
            f"{nome}: tipos das colunas",
            tipos_invalidos,
            {},
            f"Tipos incorretos: {tipos_invalidos}"
        )

    # ========================================
    # TESTES: VENDAS TEMPORAIS
    # ========================================

    def teste_vendas_temporais_estrutura(self):
        """Testa estrutura e completude de vendas_temporais."""
        print("\n📊 Testando: vendas_temporais")

        df = self.spark.table(f"{self.catalog}.{SCHEMA_GOLD}.vendas_temporais")

        # Contagem de linhas
        count_linhas = df.count()
        self.assert_equal(
            "vendas_temporais: contagem de linhas",
            count_linhas,
            EXPECTED_VALUES["total_linhas_vendas_temporais"],
            f"Linhas: {count_linhas}"
        )

        # Colunas obrigatórias sem nulos
        self.assert_not_null(
            "vendas_temporais: colunas obrigatórias",
            df,
            ["data", "dia_semana", "hora", "canal_venda", "receita", "total_vendas"]
        )

        # Valores positivos
        self.assert_positive(
            "vendas_temporais: valores positivos",
            df,
            ["receita", "total_vendas", "itens_vendidos"]
        )

        # Receita total
        receita = df.agg(sql_sum("receita")).collect()[0][0]
        self.assert_close(
            "vendas_temporais: receita total",
            receita,
            EXPECTED_VALUES["receita_total"]
        )

        # Total de vendas
        vendas = df.agg(sql_sum("total_vendas")).collect()[0][0]
        self.assert_equal(
            "vendas_temporais: total de vendas",
            vendas,
            EXPECTED_VALUES["total_vendas"]
        )

    # ========================================
    # TESTES: VENDAS PRODUTOS
    # ========================================

    def teste_vendas_produtos_estrutura(self):
        """Testa estrutura e agregações de vendas_produtos."""
        print("\n📦 Testando: vendas_produtos")

        df = self.spark.table(f"{self.catalog}.{SCHEMA_GOLD}.vendas_produtos")

        # Produto único
        duplicados = df.groupBy("id_produto").count().filter(col("count") > 1).count()
        self.assert_equal(
            "vendas_produtos: id_produto único",
            duplicados,
            0,
            f"Produtos duplicados: {duplicados}"
        )

        # Valores positivos
        self.assert_positive(
            "vendas_produtos: valores positivos",
            df,
            ["receita", "total_vendas", "itens_vendidos"]
        )

        # Ranking sequencial
        max_rank = df.agg({"ranking_receita": "max"}).collect()[0][0]
        count_produtos = df.count()
        self.assert_equal(
            "vendas_produtos: ranking sequencial",
            max_rank,
            count_produtos,
            f"Max ranking: {max_rank}, Total produtos: {count_produtos}"
        )

    # ========================================
    # TESTES: CLIENTES SEGMENTAÇÃO
    # ========================================

    def teste_clientes_segmentacao(self):
        """Testa segmentação e regras de negócio de clientes."""
        print("\n👥 Testando: clientes_segmentacao")

        df = self.spark.table(f"{self.catalog}.{SCHEMA_GOLD}.clientes_segmentacao")

        # Total de clientes
        count_clientes = df.count()
        self.assert_equal(
            "clientes_segmentacao: total de clientes",
            count_clientes,
            EXPECTED_VALUES["total_clientes"]
        )

        # Clientes VIP
        vip_count = df.filter(col("segmento_cliente") == "VIP").count()
        self.assert_equal(
            "clientes_segmentacao: clientes VIP",
            vip_count,
            EXPECTED_VALUES["clientes_vip"]
        )

        # Receita VIP
        vip_receita = df.filter(col("segmento_cliente") == "VIP") \
            .agg(sql_sum("receita")).collect()[0][0]
        self.assert_close(
            "clientes_segmentacao: receita VIP",
            vip_receita,
            EXPECTED_VALUES["receita_vip"]
        )

        # Regras de segmentação
        vip_invalidos = df.filter(
            (col("segmento_cliente") == "VIP") & (col("receita") < 22000)
        ).count()
        self.assert_equal(
            "clientes_segmentacao: regra VIP (≥22k)",
            vip_invalidos,
            0,
            f"Clientes VIP com receita < 22k: {vip_invalidos}"
        )

        top_tier_invalidos = df.filter(
            (col("segmento_cliente") == "TOP_TIER") & 
            ((col("receita") < 17000) | (col("receita") >= 22000))
        ).count()
        self.assert_equal(
            "clientes_segmentacao: regra TOP_TIER (17k-22k)",
            top_tier_invalidos,
            0,
            f"Clientes TOP_TIER fora da faixa: {top_tier_invalidos}"
        )

        # Ticket médio consistente
        df_validacao = df.withColumn(
            "ticket_calculado",
            sql_round(col("receita") / col("total_compras"), 2)
        )
        inconsistentes = df_validacao.filter(
            sql_abs(col("ticket_medio") - col("ticket_calculado")) > 0.02
        ).count()
        self.assert_equal(
            "clientes_segmentacao: ticket médio consistente",
            inconsistentes,
            0,
            f"Registros com ticket médio inconsistente: {inconsistentes}"
        )

    # ========================================
    # TESTES: PREÇOS COMPETITIVIDADE
    # ========================================

    def teste_precos_competitividade(self):
        """Testa lógica de pricing e classificação."""
        print("\n💰 Testando: precos_competitividade")

        df = self.spark.table(f"{self.catalog}.{SCHEMA_GOLD}.precos_competitividade")

        # Total de produtos monitorados
        count_produtos = df.count()
        self.assert_equal(
            "precos_competitividade: produtos monitorados",
            count_produtos,
            EXPECTED_VALUES["produtos_monitorados"]
        )

        # Produtos mais caros que todos
        mais_caros = df.filter(
            col("classificacao_preco") == "MAIS_CARO_QUE_TODOS"
        ).count()
        self.assert_equal(
            "precos_competitividade: mais caros que todos",
            mais_caros,
            EXPECTED_VALUES["produtos_mais_caros_todos"]
        )

        # Validar preços positivos
        self.assert_positive(
            "precos_competitividade: preços positivos",
            df,
            ["nosso_preco", "preco_minimo_concorrentes", "preco_maximo_concorrentes"]
        )

        # Diferença percentual consistente
        df_validacao = df.withColumn(
            "diferenca_calculada",
            sql_round(
                (col("nosso_preco") - col("preco_medio_concorrentes")) / 
                col("preco_medio_concorrentes") * 100,
                2
            )
        )
        inconsistentes = df_validacao.filter(
            sql_abs(col("diferenca_pct_vs_media") - col("diferenca_calculada")) > 0.1
        ).count()
        self.assert_equal(
            "precos_competitividade: diferença % consistente",
            inconsistentes,
            0,
            f"Registros com diferença % inconsistente: {inconsistentes}"
        )

    # ========================================
    # TESTES: VENDAS DETALHADAS
    # ========================================

    def teste_vendas_detalhadas_integridade(self):
        """Testa integridade referencial e agregações."""
        print("\n🔗 Testando: vendas_detalhadas")

        df = self.spark.table(f"{self.catalog}.{SCHEMA_GOLD}.vendas_detalhadas")

        # Total de vendas
        count_vendas = df.count()
        self.assert_equal(
            "vendas_detalhadas: total de vendas",
            count_vendas,
            EXPECTED_VALUES["total_vendas"]
        )

        # Receita total
        receita = df.agg(sql_sum("receita")).collect()[0][0]
        self.assert_close(
            "vendas_detalhadas: receita total",
            receita,
            EXPECTED_VALUES["receita_total"]
        )

        # Integridade referencial: clientes
        df_clientes = self.spark.table(f"{self.catalog}.{SCHEMA_GOLD}.clientes_segmentacao")
        vendas_sem_cliente = df.join(
            df_clientes,
            df.id_cliente == df_clientes.id_cliente,
            "left_anti"
        ).count()
        self.assert_equal(
            "vendas_detalhadas: integridade clientes",
            vendas_sem_cliente,
            0,
            f"Vendas sem cliente correspondente: {vendas_sem_cliente}"
        )

        # Integridade referencial: produtos cadastrados
        df_produtos = self.spark.table(
            f"{self.catalog}.silver.produtos"
        )

        vendas_registradas_sem_catalogo = (
            df
            .filter(col("produto_cadastrado"))
            .join(
                df_produtos,
                df.id_produto == df_produtos.id_produto,
                "left_anti"
            )
            .count()
        )

        self.assert_equal(
            "vendas_detalhadas: produtos cadastrados existem no catálogo",
            vendas_registradas_sem_catalogo,
            0,
            (
                "Vendas marcadas como cadastradas sem produto correspondente "
                f"no catálogo: {vendas_registradas_sem_catalogo}"
            )
        )

        # Produtos não cadastrados devem permanecer na Gold
        vendas_nao_cadastradas = (
            df
            .filter(~col("produto_cadastrado"))
            .count()
        )

        vendas_nao_cadastradas_silver = (
            self.spark
            .table(f"{self.catalog}.silver.vendas")
            .filter(~col("produto_cadastrado"))
            .count()
        )

        self.assert_equal(
            "vendas_detalhadas: preservação de vendas sem produto cadastrado",
            vendas_nao_cadastradas,
            vendas_nao_cadastradas_silver,
            (
                "Gold: "
                f"{vendas_nao_cadastradas}; "
                "Silver: "
                f"{vendas_nao_cadastradas_silver}"
            )
        )

    # ========================================
    # TESTES: CROSS-TABLE
    # ========================================

    def teste_consistencia_cross_table(self):
        """Testa consistência entre tabelas."""
        print("\n🔄 Testando: consistência entre tabelas")

        # Receita: vendas_temporais vs vendas_produtos vs vendas_detalhadas
        receita_temporal = self.spark.table(f"{self.catalog}.{SCHEMA_GOLD}.vendas_temporais") \
            .agg(sql_sum("receita")).collect()[0][0]

        receita_produtos = self.spark.table(f"{self.catalog}.{SCHEMA_GOLD}.vendas_produtos") \
            .agg(sql_sum("receita")).collect()[0][0]

        receita_detalhadas = self.spark.table(f"{self.catalog}.{SCHEMA_GOLD}.vendas_detalhadas") \
            .agg(sql_sum("receita")).collect()[0][0]

        self.assert_close(
            "cross-table: receita temporal vs detalhadas",
            receita_temporal,
            receita_detalhadas
        )

        self.assert_close(
            "cross-table: receita produtos vs detalhadas",
            receita_produtos,
            receita_detalhadas
        )

        # Total vendas: vendas_temporais vs vendas_detalhadas
        vendas_temporal = self.spark.table(f"{self.catalog}.{SCHEMA_GOLD}.vendas_temporais") \
            .agg(sql_sum("total_vendas")).collect()[0][0]

        vendas_detalhadas = self.spark.table(f"{self.catalog}.{SCHEMA_GOLD}.vendas_detalhadas").count()

        self.assert_equal(
            "cross-table: total vendas temporal vs detalhadas",
            vendas_temporal,
            vendas_detalhadas
        )

    # ========================================
    # TESTES: SCHEMA GOLD
    # ========================================

    def teste_schemas_gold(self):
        """Valida colunas e tipos das tabelas Gold."""
        print("\n🧱 Testando: schemas Gold")

        schemas_esperados = {
            "vendas_temporais": {
                "data": "date",
                "dia_semana": "string",
                "dia_semana_num": "int",
                "hora": "int",
                "canal_venda": "string",
                "total_vendas": "bigint",
                "itens_vendidos": "bigint",
                "receita": "decimal(20,2)",
                "clientes_unicos": "bigint",
            },

            "clientes_segmentacao": {
                "id_cliente": "string",
                "nome_cliente": "string",
                "estado": "string",
                "nome_estado": "string",
                "regiao": "string",
                "total_compras": "bigint",
                "receita": "decimal(20,2)",
                "ticket_medio": "decimal(11,2)",
                "primeira_compra": "date",
                "ultima_compra": "date",
                "segmento_cliente": "string",
                "ranking_receita": "int",
            },

            "vendas_detalhadas": {
                "id_venda": "string",
                "data_venda": "timestamp",
                "data": "date",
                "dia_semana": "string",
                "dia_semana_num": "int",
                "hora": "int",
                "canal_venda": "string",
                "id_produto": "string",
                "nome_produto": "string",
                "categoria": "string",
                "marca": "string",
                "faixa_preco": "string",
                "produto_cadastrado": "boolean",
                "id_cliente": "string",
                "nome_cliente": "string",
                "estado": "string",
                "regiao": "string",
                "segmento_cliente": "string",
                "quantidade": "bigint",
                "preco_unitario": "decimal(10,2)",
                "receita": "decimal(10,2)",
                "venda_antes_do_cadastro": "boolean",
            },

            "precos_competitividade": {
                "id_produto": "string",
                "nome_produto": "string",
                "categoria": "string",
                "marca": "string",
                "nosso_preco": "decimal(10,2)",
                "preco_medio_concorrentes": "decimal(11,2)",
                "preco_minimo_concorrentes": "decimal(10,2)",
                "preco_maximo_concorrentes": "decimal(10,2)",
                "total_concorrentes": "bigint",
                "diferenca_pct_vs_media": "decimal(19,2)",
                "diferenca_pct_vs_minimo": "decimal(18,2)",
                "classificacao_preco": "string",
                "possui_preco_suspeito": "boolean",
                "receita": "decimal(20,2)",
                "itens_vendidos": "bigint",
            },

            "qualidade_dados": {
                "regra": "string",
                "tabela": "string",
                "severidade": "string",
                "linhas_afetadas": "bigint",
                "receita_afetada": "decimal(20,2)",
            },
        }

        for tabela, schema_esperado in schemas_esperados.items():
            df = self.spark.table(
                f"{self.catalog}.{SCHEMA_GOLD}.{tabela}"
            )

            self.assert_schema(
                f"{tabela}: schema",
                df,
                schema_esperado
            )

    # ========================================
    # TESTES: CHAVES E GRANULARIDADE
    # ========================================

    def teste_chaves_e_granularidade(self):
        """Valida as chaves e granularidades das tabelas Gold."""
        print("\n🔑 Testando: chaves e granularidade")

        testes = [
            (
                "vendas_produtos",
                ["id_produto"],
            ),
            (
                "clientes_segmentacao",
                ["id_cliente"],
            ),
            (
                "vendas_detalhadas",
                ["id_venda"],
            ),
            (
                "precos_competitividade",
                ["id_produto"],
            ),
            (
                "vendas_temporais",
                [
                    "data",
                    "hora",
                    "canal_venda",
                ],
            ),
        ]

        for tabela, colunas_chave in testes:
            df = self.spark.table(
                f"{self.catalog}.{SCHEMA_GOLD}.{tabela}"
            )

            duplicados = (
                df.groupBy(*colunas_chave)
                .count()
                .filter(col("count") > 1)
                .count()
            )

            self.assert_equal(
                f"{tabela}: granularidade única",
                duplicados,
                0,
                (
                    f"Registros duplicados na chave "
                    f"{colunas_chave}: {duplicados}"
                )
            )

    # ========================================
    # TESTES: COMPLETUDE
    # ========================================

    def teste_completude_gold(self):
        """Valida campos obrigatórios sem valores nulos."""
        print("\n🧹 Testando: completude das tabelas Gold")

        campos_obrigatorios = {
            "vendas_temporais": [
                "data",
                "hora",
                "canal_venda",
                "total_vendas",
                "itens_vendidos",
                "receita",
            ],

            "vendas_produtos": [
                "id_produto",
                "nome_produto",
                "categoria",
                "marca",
                "total_vendas",
                "itens_vendidos",
                "receita",
            ],

            "clientes_segmentacao": [
                "id_cliente",
                "nome_cliente",
                "estado",
                "nome_estado",
                "regiao",
                "total_compras",
                "receita",
                "segmento_cliente",
                "ranking_receita",
            ],

            "vendas_detalhadas": [
                "id_venda",
                "data_venda",
                "id_produto",
                "id_cliente",
                "canal_venda",
                "quantidade",
                "preco_unitario",
                "receita",
            ],

            "precos_competitividade": [
                "id_produto",
                "nome_produto",
                "categoria",
                "marca",
                "nosso_preco",
                "preco_medio_concorrentes",
                "preco_minimo_concorrentes",
                "preco_maximo_concorrentes",
                "total_concorrentes",
                "classificacao_preco",
            ],
        }

        for tabela, colunas in campos_obrigatorios.items():
            df = self.spark.table(
                f"{self.catalog}.{SCHEMA_GOLD}.{tabela}"
            )

            self.assert_not_null(
                f"{tabela}: completude",
                df,
                colunas
            )

    # ========================================
    # TESTES: REGRAS DE NEGÓCIO
    # ========================================

    def teste_regras_negocio(self):
        """Valida regras de negócio das tabelas Gold."""
        print("\n📐 Testando: regras de negócio")

        # ----------------------------------------
        # Segmentação de clientes
        # ----------------------------------------

        clientes = self.spark.table(
            f"{self.catalog}.{SCHEMA_GOLD}.clientes_segmentacao"
        )

        segmentos_invalidos = clientes.filter(
            ~col("segmento_cliente").isin(
                "VIP",
                "TOP_TIER",
                "REGULAR"
            )
        ).count()

        self.assert_equal(
            "clientes_segmentacao: segmentos válidos",
            segmentos_invalidos,
            0,
            f"Segmentos inválidos: {segmentos_invalidos}"
        )

        # ----------------------------------------
        # Canais de venda
        # ----------------------------------------

        vendas = self.spark.table(
            f"{self.catalog}.{SCHEMA_GOLD}.vendas_detalhadas"
        )

        canais_invalidos = vendas.filter(
            ~col("canal_venda").isin(
                "ecommerce",
                "loja_fisica"
            )
        ).count()

        self.assert_equal(
            "vendas_detalhadas: canais válidos",
            canais_invalidos,
            0,
            f"Canais inválidos: {canais_invalidos}"
        )

        # ----------------------------------------
        # Receita da venda
        # ----------------------------------------

        vendas_validacao = vendas.withColumn(
            "receita_calculada",
            (
                col("quantidade") *
                col("preco_unitario")
            ).cast("decimal(10,2)")
        )

        receita_inconsistente = vendas_validacao.filter(
            sql_abs(
                col("receita") -
                col("receita_calculada")
            ) > 0.01
        ).count()

        self.assert_equal(
            "vendas_detalhadas: receita consistente",
            receita_inconsistente,
            0,
            (
                "Vendas com receita diferente de "
                "quantidade × preço unitário: "
                f"{receita_inconsistente}"
            )
        )

        # ----------------------------------------
        # Flags booleanas
        # ----------------------------------------

        flags_invalidas = vendas.filter(
            col("produto_cadastrado").isNull() |
            col("venda_antes_do_cadastro").isNull()
        ).count()

        self.assert_equal(
            "vendas_detalhadas: flags de qualidade preenchidas",
            flags_invalidas,
            0,
            f"Flags nulas: {flags_invalidas}"
        )

    # ========================================
    # TESTES: SCORECARD DE QUALIDADE
    # ========================================

    def teste_qualidade_dados(self):
        """Valida o scorecard de qualidade contra as tabelas Silver."""
        print("\n🛡️ Testando: qualidade_dados")

        qualidade = self.spark.table(
            f"{self.catalog}.{SCHEMA_GOLD}.qualidade_dados"
        )

        regras_esperadas = [
            "Venda de produto não cadastrado",
            "Venda anterior à criação do produto",
            "Preço de concorrente abaixo de 60% do nosso",
            "Marca do produto diferente da marca citada no nome",
            "Produto com nome igual ao de outro produto",
            "Produto monitorado em menos de 4 concorrentes",
            "Nome de cliente com pronome de tratamento",
        ]

        regras_faltantes = [
            regra
            for regra in regras_esperadas
            if qualidade.filter(
                col("regra") == regra
            ).count() == 0
        ]

        self.assert_equal(
            "qualidade_dados: regras esperadas",
            regras_faltantes,
            [],
            f"Regras ausentes: {regras_faltantes}"
        )

        # Venda de produto não cadastrado
        esperado = (
            self.spark
            .table(f"{self.catalog}.silver.vendas")
            .filter(~col("produto_cadastrado"))
            .count()
        )

        obtido = (
            qualidade
            .filter(
                col("regra") ==
                "Venda de produto não cadastrado"
            )
            .select("linhas_afetadas")
            .collect()[0][0]
        )

        self.assert_equal(
            "qualidade_dados: produtos não cadastrados",
            obtido,
            esperado,
            f"Gold: {obtido}, Silver: {esperado}"
        )

        # Venda anterior à criação do produto
        esperado = (
            self.spark
            .table(f"{self.catalog}.silver.vendas")
            .filter(col("venda_antes_do_cadastro"))
            .count()
        )

        obtido = (
            qualidade
            .filter(
                col("regra") ==
                "Venda anterior à criação do produto"
            )
            .select("linhas_afetadas")
            .collect()[0][0]
        )

        self.assert_equal(
            "qualidade_dados: vendas anteriores ao cadastro",
            obtido,
            esperado,
            f"Gold: {obtido}, Silver: {esperado}"
        )

        # Preços suspeitos
        esperado = (
            self.spark
            .table(f"{self.catalog}.silver.preco_competidores")
            .filter(col("preco_suspeito"))
            .count()
        )

        obtido = (
            qualidade
            .filter(
                col("regra") ==
                "Preço de concorrente abaixo de 60% do nosso"
            )
            .select("linhas_afetadas")
            .collect()[0][0]
        )

        self.assert_equal(
            "qualidade_dados: preços suspeitos",
            obtido,
            esperado,
            f"Gold: {obtido}, Silver: {esperado}"
        )

    # ========================================
    # EXECUÇÃO E RELATÓRIO
    # ========================================

    def executar_todos(self):
        """Executa toda a bateria de testes."""
        print("=" * 70)
        print("🧪 INICIANDO TESTES DE QUALIDADE - PROJETO DADOS LAKEHOUSE")
        print("=" * 70)
        print(f"Catálogo: {self.catalog}")
        print(f"Schema: {SCHEMA_GOLD}")
        print(f"Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        print("=" * 70)

        # Executar testes
        # Testes existentes
        self.teste_vendas_temporais_estrutura()
        self.teste_vendas_produtos_estrutura()
        self.teste_clientes_segmentacao()
        self.teste_precos_competitividade()
        self.teste_vendas_detalhadas_integridade()
        self.teste_consistencia_cross_table()

        # Testes estruturais
        self.teste_schemas_gold()
        self.teste_chaves_e_granularidade()
        self.teste_completude_gold()

        # Testes de regras
        self.teste_regras_negocio()
        self.teste_qualidade_dados()

        # Relatório final
        print("\n" + "=" * 70)
        print("📊 RELATÓRIO FINAL")
        print("=" * 70)
        print(f"Total de testes: {self.total_testes}")
        print(f"Testes passaram: {self.testes_passaram} ✅")
        print(f"Testes falharam: {self.total_testes - self.testes_passaram} ❌")
        print(f"Taxa de sucesso: {self.testes_passaram / self.total_testes * 100:.1f}%")

        if self.testes_passaram == self.total_testes:
            print("\n🎉 TODOS OS TESTES PASSARAM! QUALIDADE VALIDADA.")
        else:
            print("\n⚠️ ALGUNS TESTES FALHARAM. REVISAR DADOS.")
            print("\nTestes que falharam:")
            for resultado in self.resultados:
                if not resultado["passou"]:
                    print(f"  ❌ {resultado['teste']}")
                    if resultado["mensagem"]:
                        print(f"     {resultado['mensagem']}")

        print("=" * 70)

        return self.testes_passaram == self.total_testes


# ========================================
# MAIN
# ========================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Executa os testes de qualidade das tabelas Gold."
    )

    parser.add_argument(
        "--catalog",
        default=CATALOG,
        help="Catálogo Unity Catalog onde estão as tabelas do projeto.",
    )

    args = parser.parse_args()

    spark = SparkSession.builder.getOrCreate()

    testes = TestesQualidadeDados(
        spark=spark,
        catalog=args.catalog,
    )

    sucesso = testes.executar_todos()

    import sys
    sys.exit(0 if sucesso else 1)
