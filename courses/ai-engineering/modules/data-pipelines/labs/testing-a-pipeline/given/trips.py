"""August 2025's yellow and green cab trips as one table."""

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F

YELLOW = "data/yellow_tripdata_2025-08.parquet"
GREEN = "data/green_tripdata_2025-08.parquet"

# The table's columns: each one's name, its type, and its column in the files, whose
# pickup and drop-off times start with the service's prefix.
COLUMNS = [
    ("vendor", "int", "VendorID"),
    ("pickup_at", "timestamp_ntz", "{prefix}_pickup_datetime"),
    ("dropoff_at", "timestamp_ntz", "{prefix}_dropoff_datetime"),
    ("passengers", "int", "passenger_count"),
    ("distance", "double", "trip_distance"),
    ("pickup_zone", "int", "PULocationID"),
    ("dropoff_zone", "int", "DOLocationID"),
    ("payment", "int", "payment_type"),
    ("fare", "double", "fare_amount"),
    ("tip", "double", "tip_amount"),
    ("total", "double", "total_amount"),
]


def service(spark: SparkSession, path: str, name: str, prefix: str) -> DataFrame:
    """One service's trips, in the table's columns and types."""
    return spark.read.parquet(path).select(
        F.lit(name).alias("service"),
        *[
            F.col(source.format(prefix=prefix)).cast(kind).alias(column)
            for column, kind, source in COLUMNS
        ],
    )


def trips(spark: SparkSession) -> DataFrame:
    """Every yellow and green trip in the month's files, with the service of each."""
    yellow = service(spark, YELLOW, "yellow", "tpep")
    green = service(spark, GREEN, "green", "lpep")
    return yellow.unionByName(green)
