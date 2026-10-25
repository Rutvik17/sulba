"""Each zone's clean pickups day by day, and each borough's busiest zones."""

from pyspark.sql import Column, DataFrame, SparkSession, Window
from pyspark.sql import functions as F

ZONES = "data/taxi_zone_lookup.csv"

# What the zone lookup writes where it has no borough or name.
MISSING = ["N/A", "Unknown"]

# The first day whose seven days ending on it all fall in August.
FIRST_WEEK = "2025-08-07"


def zones(spark: SparkSession) -> DataFrame:
    """The city's zones: each one's number, borough and name, missing where the lookup has
    none."""
    lookup = spark.read.option("header", True).csv(ZONES)

    def known(column: str) -> Column:
        return F.when(~F.col(column).isin(MISSING), F.col(column))

    return lookup.select(
        F.col("LocationID").cast("int").alias("zone"),
        known("Borough").alias("borough"),
        known("Zone").alias("name"),
    )


def zone_days(flagged: DataFrame, zones: DataFrame) -> DataFrame:
    """A row for each zone and day with clean pickups: the zone, its borough and name, the day,
    its trips, and `week`, the zone's mean trips a day over the seven days ending that day, a day
    with none counting as 0, from 7 August."""
    days = (
        flagged.where("clean")
        .groupBy(
            F.col("pickup_zone").alias("zone"), F.to_date("pickup_at").alias("day")
        )
        .agg(F.count("*").alias("trips"))
    )
    # Days since the month began, so the frame covers seven days of the calendar, not seven rows.
    number = F.datediff("day", F.lit("2025-08-01").cast("date"))
    seven = Window.partitionBy("zone").orderBy(number).rangeBetween(-6, 0)
    week = F.when(
        F.col("day") >= F.lit(FIRST_WEEK).cast("date"), F.sum("trips").over(seven) / 7
    )
    return days.join(F.broadcast(zones), "zone").select(
        "zone", "borough", "name", "day", "trips", week.alias("week")
    )


def busiest(zone_days: DataFrame, n: int = 3) -> DataFrame:
    """Each borough's n busiest zones each day by trips, with their place, zones that tie
    sharing one."""
    place = F.rank().over(Window.partitionBy("borough", "day").orderBy(F.desc("trips")))
    return zone_days.select(
        "borough", "day", place.alias("place"), "zone", "name", "trips"
    ).where(F.col("place") <= n)
