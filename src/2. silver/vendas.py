from pyspark import pipelines as dp
from pyspark.sql import functions as F

DINHEIRO = "decimal(10,2)"

DIAS = {
    "Sunday": "Domingo",
    "Monday": "Segunda",
    "Tuesday": "Terça",
    "Wednesday": "Quarta",
    "Thursday": "Quinta",
    "Friday": "Sexta",
    "Saturday": "Sábado",
}

TRADUCAO = F.create_map(
    [F.lit(x) for par in DIAS.items() for x in par]
)

@dp.materialized_view(
    comment="Uma linha por venda, com receita, calendário e marcações de qualidade."
)
@dp.expect_all_or_fail({
    "campos_obrigatorios": (
        "id_venda IS NOT NULL "
        "AND data_venda IS NOT NULL "
        "AND id_cliente IS NOT NULL "
        "AND id_produto IS NOT NULL "
        "AND quantidade IS NOT NULL "
        "AND preco_unitario IS NOT NULL"
    ),
    "quantidade_positiva": "quantidade > 0",
    "preco_positivo": "preco_unitario > 0",
    "canal_conhecido": (
        "canal_venda IN ('ecommerce', 'loja_fisica')"
    ),
})
@dp.expect_all({
    "produto_cadastrado": "produto_cadastrado",
    "venda_depois_do_cadastro": "venda_depois_do_cadastro",
    "venda_nao_antecede_cadastro": "NOT venda_antes_do_cadastro",
})
def vendas():

    cadastro = (
        spark.read.table("silver.produtos")
        .select(
            "id_produto",
            F.lit(True).alias("produto_cadastrado"),
            "data_criacao",
        )
    )

    return (
        spark.read.table("bronze.vendas")
        .dropDuplicates(["id_venda"])

        # Padronização de tipos
        .withColumn(
            "preco_unitario",
            F.col("preco_unitario").cast(DINHEIRO)
        )

        # Receita da venda
        .withColumn(
            "receita",
            (
                F.col("quantidade") * F.col("preco_unitario")
            ).cast(DINHEIRO)
        )

        # Calendário
        .withColumn(
            "data",
            F.to_date("data_venda")
        )
        .withColumn(
            "hora",
            F.hour("data_venda")
        )
        .withColumn(
            "dia_semana_num",
            F.dayofweek("data_venda")
        )
        .withColumn(
            "dia_semana",
            TRADUCAO[
                F.date_format("data_venda", "EEEE")
            ]
        )

        # Enriquecimento com cadastro dos produtos
        .join(
            cadastro,
            on="id_produto",
            how="left",
        )

        # Produto existe no cadastro?
        .withColumn(
            "produto_cadastrado",
            F.coalesce(
                F.col("produto_cadastrado"),
                F.lit(False),
            )
        )

        # Venda realizada antes da criação do produto
        .withColumn(
            "venda_antes_do_cadastro",
            F.coalesce(
                F.col("data_venda") < F.col("data_criacao"),
                F.lit(False),
            )
        )

        # Venda realizada após ou no momento da criação do produto
        .withColumn(
            "venda_depois_do_cadastro",
            F.coalesce(
                F.col("produto_cadastrado")
                & (
                    F.col("data_venda")
                    >= F.col("data_criacao")
                ),
                F.lit(False),
            )
        )

        # A data de criação já foi utilizada nas regras de qualidade.
        .drop("data_criacao")
    )