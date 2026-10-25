"""Each borough's clean pickups on each day of August, with the day's weather."""

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F

ZONES = "data/taxi_zone_lookup.csv"

# What the zone lookup writes where it has no borough.
MISSING = ["N/A", "Unknown"]

# Rain from which a day counts as wet, in millimetres.
WET_MM = 1.0


def august(spark: SparkSession) -> DataFrame:
    """Every day of August 2025, one row each, in `day`."""
    start = F.lit("2025-08-01").cast("date")
    return spark.range(31).select(
        F.date_add(start, F.col("id").cast("int")).alias("day")
    )


def boroughs(spark: SparkSession) -> DataFrame:
    """Each zone's number and borough, the borough missing where the lookup has none."""
    lookup = spark.read.option("header", True).csv(ZONES)
    return lookup.select(
        F.col("LocationID").cast("int").alias("zone"),
        F.when(~F.col("Borough").isin(MISSING), F.col("Borough")).alias("borough"),
    )


def daily(spark: SparkSession, flagged: DataFrame, weather: DataFrame) -> DataFrame:
    """A row for each day of August and each borough: the day, its weekday, the borough, its
    clean pickups that day, the day's weather, and whether it was wet. A borough with no
    clean pickups on a day has 0 of them, and a day the weather lacks has no weather."""
    zones = boroughs(spark)
    names = zones.where(F.col("borough").isNotNull()).select("borough").distinct()
    grid = august(spark).crossJoin(names)
    trips = (
        flagged.where("clean")
        .join(F.broadcast(zones), F.col("pickup_zone") == F.col("zone"))
        .groupBy(F.to_date("pickup_at").alias("day"), "borough")
        .agg(F.count("*").alias("trips"))
    )
    return (
        grid.join(trips, ["day", "borough"], "left")
        .join(weather, "day", "left")
        .select(
            "day",
            F.date_format("day", "EEEE").alias("weekday"),
            "borough",
            F.coalesce("trips", F.lit(0)).alias("trips"),
            *[column for column in weather.columns if column != "day"],
            (F.col("rain_mm") >= WET_MM).alias("wet"),
        )
    )
