"""Central Park's August 2025 weather, one row a day, from NOAA's daily summaries."""

from pyspark.sql import Column, DataFrame, SparkSession
from pyspark.sql import functions as F

WEATHER = "data/central-park-2025-08.csv"

# The weather types the file marks with a 1 on the days they were seen.
TYPES = {"fog": "WT01", "thunder": "WT03", "haze": "WT08"}


def attribute(column: str, position: int) -> Column:
    """One of a value's attributes: its measurement flag (0), quality flag (1), source flag (2)
    or time of observation (3), an empty string where it has none."""
    return F.coalesce(F.split(F.col(f"{column}_ATTRIBUTES"), ",")[position], F.lit(""))


def measured(column: str) -> Column:
    """A value the file gives in tenths of its unit, as a number of units, missing where it
    failed a quality check."""
    value = F.trim(F.col(column)).cast("int") / 10
    return F.when(attribute(column, 1) == "", value)


def weather(spark: SparkSession) -> DataFrame:
    """A row for each day in the file: the day, its rain, whether only a trace fell, its high and
    low, its mean wind, and whether fog, thunder or haze were seen."""
    raw = spark.read.option("header", True).csv(WEATHER)
    seen = [
        F.coalesce(F.trim(F.col(column)) == "1", F.lit(False)).alias(name)
        for name, column in TYPES.items()
    ]
    return raw.select(
        F.to_date("DATE").alias("day"),
        measured("PRCP").alias("rain_mm"),
        (attribute("PRCP", 0) == "T").alias("trace"),
        measured("TMAX").alias("high_c"),
        measured("TMIN").alias("low_c"),
        measured("AWND").alias("wind_ms"),
        *seen,
    )
