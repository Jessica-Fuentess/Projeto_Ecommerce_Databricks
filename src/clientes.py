# Silver · clientes
#
# Dois cuidados com o cliente:
# - 11 dos 50 nomes chegam com pronome de tratamento ("Sr.", "Dra."...). O nome limpo
#   agrupa e ordena melhor; o original fica guardado em `nome_original`.
# - O cliente só tem a UF. Não existe tabela de estados na bronze, então o mapeamento
#   das 27 UFs do IBGE (sigla → nome e região) é declarado aqui mesmo, no arquivo.
#   A diretoria de Customer Success usa a região para dividir a carteira.

from pyspark import pipelines as dp
from pyspark.sql import functions as F
from pyspark.sql import types as T

TRATAMENTO = r"^(Sr|Sra|Srta|Dr|Dra)\.\s+"

# Mapeamento fixo das 27 UFs do IBGE: (sigla, nome do estado, região)
# Declarado aqui porque não existe tabela de estados na bronze.
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
    # UF que não existe no IBGE ficaria sem região e sumiria dos gráficos por região
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
