from pyspark import pipelines as dp
from pyspark.sql import functions as F

TRATAMENTO = r"^(Sr|Sra|Srta|Dr|Dra)\.\s+"

ESTADOS_IBGE = [
    # Norte
    ("AC", "Acre", "Norte"),
    ("AM", "Amazonas", "Norte"),
    ("AP", "Amapá", "Norte"),
    ("PA", "Pará", "Norte"),
    ("RO", "Rondônia", "Norte"),
    ("RR", "Roraima", "Norte"),
    ("TO", "Tocantins", "Norte"),
    # Nordeste
    ("AL", "Alagoas", "Nordeste"),
    ("BA", "Bahia", "Nordeste"),
    ("CE", "Ceará", "Nordeste"),
    ("MA", "Maranhão", "Nordeste"),
    ("PB", "Paraíba", "Nordeste"),
    ("PE", "Pernambuco", "Nordeste"),
    ("PI", "Piauí", "Nordeste"),
    ("RN", "Rio Grande do Norte", "Nordeste"),
    ("SE", "Sergipe", "Nordeste"),
    # Centro-Oeste
    ("DF", "Distrito Federal", "Centro-Oeste"),
    ("GO", "Goiás", "Centro-Oeste"),
    ("MT", "Mato Grosso", "Centro-Oeste"),
    ("MS", "Mato Grosso do Sul", "Centro-Oeste"),
    # Sudeste
    ("ES", "Espírito Santo", "Sudeste"),
    ("MG", "Minas Gerais", "Sudeste"),
    ("RJ", "Rio de Janeiro", "Sudeste"),
    ("SP", "São Paulo", "Sudeste"),
    # Sul
    ("PR", "Paraná", "Sul"),
    ("RS", "Rio Grande do Sul", "Sul"),
    ("SC", "Santa Catarina", "Sul"),
]


@dp.materialized_view(comment="Clientes com nome limpo, UF padronizada e região do IBGE.")
@dp.expect_all_or_fail({
    "id_cliente_preenchido": "id_cliente IS NOT NULL",
    "cliente_com_regiao": "regiao IS NOT NULL",
})
def clientes():
    estados = spark.createDataFrame(
        ESTADOS_IBGE,
        schema="estado string, nome_estado string, regiao string",
    )

    return (
        spark.read.table("bronze.clientes")
        .dropDuplicates(["id_cliente"])
        .withColumn("nome_original", F.trim("nome_cliente"))
        .withColumn("nome_cliente", F.initcap(F.regexp_replace("nome_original", TRATAMENTO, "")))
        .withColumn("estado", F.upper(F.trim("estado")))
        .join(estados, on="estado", how="left")
    )
