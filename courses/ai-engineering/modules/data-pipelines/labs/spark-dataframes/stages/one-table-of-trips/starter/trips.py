"""August 2025's yellow and green cab trips as one table."""

from pyspark.sql import DataFrame, SparkSession


def trips(spark: SparkSession) -> DataFrame:
    """Every yellow and green trip in the month's files, with the service of each."""
    raise NotImplementedError
