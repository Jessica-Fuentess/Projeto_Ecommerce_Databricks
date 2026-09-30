from pyspark import pipelines as dp
from pyspark.sql import functions as F

DINHEIRO = "decimal(10,2)"

@dp.materialized_view(comment="Catálogo de produtos limpo: preço em DECIMAL e faixa de preço.")
@dp.expect_all_or_fail({
    "id_produto_preenchido": "id_produto IS NOT NULL",
    "preco_positivo": "preco_atual > 0",
})
def produtos():
    return (
        spark.read.table("bronze.produtos")
        .dropDuplicates(["id_produto"])
        .withColumn("nome_produto", F.trim("nome_produto"))
        .withColumn("preco_atual", F.col("preco_atual").cast(DINHEIRO))
        .withColumn(
            "faixa_preco",
            F.when(F.col("preco_atual") > 1000, "PREMIUM")
            .when(F.col("preco_atual") > 500, "MEDIO")
            .otherwise("BASICO"),
        )
    )
