"""The month's report for the dispatcher: each service's trips and takings, day by day."""

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F

YELLOW = "data/yellow_tripdata_2025-08.parquet"
GREEN = "data/green_tripdata_2025-08.parquet"

# The columns the report adds up.
AMOUNTS = [
    "payment_type",
    "fare_amount",
    "tip_amount",
    "total_amount",
    "congestion_surcharge",
    "cbd_congestion_fee",
]


def service(spark: SparkSession, path: str, name: str, prefix: str) -> DataFrame:
    """One service's trips: its name, the pickup time and the amounts, as doubles."""
    trips = spark.read.parquet(path)
    return trips.select(
        F.lit(name).alias("service"),
        F.col(f"{prefix}_pickup_datetime").alias("pickup_at"),
        *[
            F.col(column).cast("double")
            for column in trips.columns
            if column in AMOUNTS
        ],
    )


def daily_report(spark: SparkSession) -> DataFrame:
    """Each service's trips on each day of August: how many, how many paid by card, the
    fares, tips and takings, and the congestion charges collected."""
    yellow = service(spark, YELLOW, "yellow", "tpep")
    green = service(spark, GREEN, "green", "lpep")
    trips = yellow.unionByName(green)
    return (
        trips.where((F.year("pickup_at") == 2025) & (F.month("pickup_at") == 8))
        .groupBy("service", F.dayofmonth("pickup_at").alias("day"))
        .agg(
            F.count("*").alias("trips"),
            F.count_if(F.col("payment_type") == 1).alias("card_trips"),
            F.sum("fare_amount").alias("fares"),
            F.sum("tip_amount").alias("tips"),
            F.sum("total_amount").alias("takings"),
            (F.sum("congestion_surcharge") + F.sum("cbd_congestion_fee")).alias(
                "charges"
            ),
        )
    )
