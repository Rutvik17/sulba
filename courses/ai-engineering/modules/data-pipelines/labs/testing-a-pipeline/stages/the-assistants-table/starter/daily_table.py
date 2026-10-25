"""The daily table: each borough's clean pickups on each day of August, with the weather."""

from pyspark.sql import Column, DataFrame, SparkSession
from pyspark.sql import functions as F

from flags import flagged
from trips import trips

WEATHER = "data/central-park-2025-08.csv"
ZONES = "data/taxi_zone_lookup.csv"
WEEKDAYS = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]


def value(column: str) -> Column:
    """A weather value in its units, missing where it failed a quality check."""
    flag = F.coalesce(F.split(F.col(f"{column}_ATTRIBUTES"), ",")[0], F.lit(""))
    return F.when(flag == "", F.trim(F.col(column)).cast("int") / 10)


def daily_table(spark: SparkSession) -> DataFrame:
    """A row for each day of August and each borough: the day, its weekday, the borough, its
    clean pickups, the day's rain and high, and whether it was wet."""
    weather = (
        spark.read.option("header", True)
        .csv(WEATHER)
        .select(
            F.to_date("DATE").alias("day"),
            value("PRCP").alias("rain_mm"),
            value("TMAX").alias("high_c"),
        )
    )
    zones = (
        spark.read.option("header", True)
        .csv(ZONES)
        .select(
            F.col("LocationID").cast("int").alias("zone"),
            F.col("Borough").alias("borough"),
        )
    )
    counts = (
        flagged(trips(spark))
        .where("clean")
        .join(F.broadcast(zones), F.col("pickup_zone") == F.col("zone"))
        .groupBy(F.to_date("pickup_at").alias("day"), "borough")
        .agg(F.count("passengers").alias("trips"))
    )
    start = F.lit("2025-08-01").cast("date")
    days = spark.range(31).select(
        F.date_add(start, F.col("id").cast("int")).alias("day")
    )
    names = (
        zones.where(~F.col("borough").isin("N/A", "Unknown"))
        .select("borough")
        .distinct()
    )
    weekdays = F.array(*[F.lit(name) for name in WEEKDAYS])
    return (
        days.crossJoin(names)
        .join(counts, ["day", "borough"])
        .join(weather, "day", "left")
        .select(
            "day",
            F.element_at(weekdays, F.dayofweek("day")).alias("weekday"),
            "borough",
            F.coalesce("trips", F.lit(0)).alias("trips"),
            "rain_mm",
            "high_c",
            (F.col("rain_mm") >= 1.0).alias("wet"),
        )
    )
