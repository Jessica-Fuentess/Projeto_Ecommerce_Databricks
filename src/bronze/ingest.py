import argparse

from pyspark.sql import SparkSession
from pyspark.sql import functions as F

CATALOG = "projeto_dados"
SCHEMA = "bronze"

def carregar_csv(
    spark: SparkSession,
    caminho: str,
    tabela: str,
    colunas: list[str],
    casts: dict[str, str],
    catalogo: str,
) -> None:
    """
    Lê um CSV da pasta de dados e substitui os dados da tabela Bronze.
    A estrutura da tabela é definida previamente pelo bronze_schema.sql.
    """

    df = (
        spark.read
        .option("header", "true")
        .option("inferSchema", "false")
        .csv(caminho)
    )

    df = df.select(*colunas)

    for coluna, tipo in casts.items():
        df = df.withColumn(
            coluna,
            F.col(coluna).cast(tipo)
        )

    nome_tabela = f"{catalogo}.{SCHEMA}.{tabela}"

    (
        df.write
        .mode("overwrite")
        .insertInto(nome_tabela)
    )

    print(
        f"[OK] {nome_tabela}: "
        f"{df.count()} registros carregados."
    )

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Ingestão dos arquivos CSV para a camada Bronze."
    )

    parser.add_argument(
        "--data-path",
        required=True,
        help="Caminho absoluto da pasta data no Workspace.",
    )

    parser.add_argument(
        "--catalog",
        default=CATALOG,
        help="Catálogo Unity Catalog onde estão as tabelas Bronze.",
    )

    args = parser.parse_args()

    spark = SparkSession.builder.getOrCreate()

    data_path = args.data_path.rstrip("/")

    carregar_csv(
        spark=spark,
        caminho=f"{data_path}/clientes.csv",
        tabela="clientes",
        colunas=[
            "id_cliente",
            "nome_cliente",
            "estado",
            "pais",
            "data_cadastro",
        ],
        casts={
            "data_cadastro": "timestamp",
        },
        catalogo=args.catalog,
    )

    carregar_csv(
        spark=spark,
        caminho=f"{data_path}/produtos.csv",
        tabela="produtos",
        colunas=[
            "id_produto",
            "nome_produto",
            "categoria",
            "marca",
            "preco_atual",
            "data_criacao",
        ],
        casts={
            "preco_atual": "double",
            "data_criacao": "timestamp",
        },
        catalogo=args.catalog,
    )

    carregar_csv(
        spark=spark,
        caminho=f"{data_path}/vendas.csv",
        tabela="vendas",
        colunas=[
            "id_venda",
            "data_venda",
            "id_cliente",
            "id_produto",
            "canal_venda",
            "quantidade",
            "preco_unitario",
        ],
        casts={
            "data_venda": "timestamp",
            "quantidade": "bigint",
            "preco_unitario": "double",
        },
        catalogo=args.catalog,
    )

    carregar_csv(
        spark=spark,
        caminho=f"{data_path}/preco_competidores.csv",
        tabela="preco_competidores",
        colunas=[
            "id_produto",
            "nome_concorrente",
            "preco_concorrente",
            "data_coleta",
        ],
        casts={
            "preco_concorrente": "double",
        },
        catalogo=args.catalog,
    )

    print("\n[OK] Ingestão Bronze concluída.")

if __name__ == "__main__":
    main()