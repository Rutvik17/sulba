"""Each borough's trips on wet days against its trips on dry days."""

from pyspark.sql import DataFrame, Window
from pyspark.sql import functions as F


def wet_and_dry(daily: DataFrame) -> DataFrame:
    """Each borough's wet and dry days: how many of each, and its mean clean pickups on them. A
    day without weather is neither."""
    wet = F.col("wet")
    return daily.groupBy("borough").agg(
        F.count_if(wet).alias("wet_days"),
        F.avg(F.when(wet, F.col("trips"))).alias("wet_trips"),
        F.count_if(~wet).alias("dry_days"),
        F.avg(F.when(~wet, F.col("trips"))).alias("dry_trips"),
    )


def against_dry_days(daily: DataFrame) -> DataFrame:
    """Each borough's wet days, each with the borough's dry days of the same weekday: how many
    there were, their mean clean pickups, and the wet day's change from that mean."""
    same = Window.partitionBy("borough", "weekday")
    dry = F.when(~F.col("wet"), F.col("trips"))
    compared = daily.select(
        "borough",
        "day",
        "weekday",
        "rain_mm",
        "trips",
        "wet",
        F.count(dry).over(same).alias("dry_days"),
        F.avg(dry).over(same).alias("dry_trips"),
    )
    change = F.when(F.col("dry_trips") > 0, F.col("trips") / F.col("dry_trips") - 1)
    return compared.where("wet").select(
        "borough",
        "day",
        "weekday",
        "rain_mm",
        "trips",
        "dry_days",
        "dry_trips",
        change.alias("change"),
    )
