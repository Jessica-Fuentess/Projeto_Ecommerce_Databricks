"""
Testes de Qualidade - Projeto Dados Lakehouse
==============================================

Script para validação automatizada da qualidade dos dados nas tabelas Gold.
Testa integridade, completude, consistência e valores esperados.

"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, count, sum as sql_sum, avg, round as sql_round, abs as sql_abs
from datetime import datetime
from typing import Dict, List

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
    "produtos_monitored": 215,
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

    def __init__(self, spark: SparkSession):
        self.spark = spark
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
            negativos = df.filter(col(coluna) < 0).count()
            passou = negativos == 0
            msg = f"Coluna '{coluna}': {negativos} valores negativos"
            self.registrar_resultado(f"{nome} - {coluna}", passou, msg)

    # ========================================
    # TESTES: VENDAS TEMPORAIS
    # ========================================

    def teste_vendas_temporais_estrutura(self):
        """Testa estrutura e completude de vendas_temporais."""
        print("\n📊 Testando: vendas_temporais")

        df = self.spark.table(f"{CATALOG}.{SCHEMA_GOLD}.vendas_temporais")

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

        df = self.spark.table(f"{CATALOG}.{SCHEMA_GOLD}.vendas_produtos")

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

        df = self.spark.table(f"{CATALOG}.{SCHEMA_GOLD}.clientes_segmentacao")

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

        df = self.spark.table(f"{CATALOG}.{SCHEMA_GOLD}.precos_competitividade")

        # Total de produtos monitorados
        count_produtos = df.count()
        self.assert_equal(
            "precos_competitividade: produtos monitorados",
            count_produtos,
            EXPECTED_VALUES["produtos_monitored"]
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

        df = self.spark.table(f"{CATALOG}.{SCHEMA_GOLD}.vendas_detalhadas")

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
        df_clientes = self.spark.table(f"{CATALOG}.{SCHEMA_GOLD}.clientes_segmentacao")
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

        # Integridade referencial: produtos
        df_produtos = self.spark.table(f"{CATALOG}.{SCHEMA_GOLD}.vendas_produtos")
        vendas_sem_produto = df.join(
            df_produtos,
            df.id_produto == df_produtos.id_produto,
            "left_anti"
        ).count()
        self.assert_equal(
            "vendas_detalhadas: integridade produtos",
            vendas_sem_produto,
            0,
            f"Vendas sem produto correspondente: {vendas_sem_produto}"
        )

    # ========================================
    # TESTES: CROSS-TABLE
    # ========================================

    def teste_consistencia_cross_table(self):
        """Testa consistência entre tabelas."""
        print("\n🔄 Testando: consistência entre tabelas")

        # Receita: vendas_temporais vs vendas_produtos vs vendas_detalhadas
        receita_temporal = self.spark.table(f"{CATALOG}.{SCHEMA_GOLD}.vendas_temporais") \
            .agg(sql_sum("receita")).collect()[0][0]

        receita_produtos = self.spark.table(f"{CATALOG}.{SCHEMA_GOLD}.vendas_produtos") \
            .agg(sql_sum("receita")).collect()[0][0]

        receita_detalhadas = self.spark.table(f"{CATALOG}.{SCHEMA_GOLD}.vendas_detalhadas") \
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
        vendas_temporal = self.spark.table(f"{CATALOG}.{SCHEMA_GOLD}.vendas_temporais") \
            .agg(sql_sum("total_vendas")).collect()[0][0]

        vendas_detalhadas = self.spark.table(f"{CATALOG}.{SCHEMA_GOLD}.vendas_detalhadas").count()

        self.assert_equal(
            "cross-table: total vendas temporal vs detalhadas",
            vendas_temporal,
            vendas_detalhadas
        )

    # ========================================
    # EXECUÇÃO E RELATÓRIO
    # ========================================

    def executar_todos(self):
        """Executa toda a bateria de testes."""
        print("=" * 70)
        print("🧪 INICIANDO TESTES DE QUALIDADE - PROJETO DADOS LAKEHOUSE")
        print("=" * 70)
        print(f"Catálogo: {CATALOG}")
        print(f"Schema: {SCHEMA_GOLD}")
        print(f"Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        print("=" * 70)

        # Executar testes
        self.teste_vendas_temporais_estrutura()
        self.teste_vendas_produtos_estrutura()
        self.teste_clientes_segmentacao()
        self.teste_precos_competitividade()
        self.teste_vendas_detalhadas_integridade()
        self.teste_consistencia_cross_table()

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
    # Obter SparkSession
    spark = SparkSession.builder.getOrCreate()

    # Criar e executar testes
    testes = TestesQualidadeDados(spark)
    sucesso = testes.executar_todos()

    # Exit code para CI/CD
    import sys
    sys.exit(0 if sucesso else 1)
