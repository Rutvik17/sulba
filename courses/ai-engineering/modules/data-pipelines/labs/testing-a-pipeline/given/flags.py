"""Flags for the trips whose records can't be taken at their word."""

from pyspark.sql import Column, DataFrame
from pyspark.sql import functions as F

# The zones the city's lookup marks as unknown and outside the city.
UNKNOWN_ZONES = [264, 265]

# The flags, in the order their columns come.
FLAGS = [
    "outside_month",
    "backwards",
    "too_long",
    "no_distance",
    "negative",
    "unknown_zone",
]


def rules() -> dict[str, Column]:
    """Each flag's condition: true when the trip's values show the problem."""
    pickup = F.col("pickup_at")
    dropoff = F.col("dropoff_at")
    return {
        "outside_month": (pickup < F.lit("2025-08-01").cast("timestamp_ntz"))
        | (pickup >= F.lit("2025-09-01").cast("timestamp_ntz")),
        "backwards": dropoff < pickup,
        "too_long": dropoff > pickup + F.expr("INTERVAL 24 HOURS"),
        "no_distance": F.col("distance") <= 0,
        "negative": (F.col("fare") < 0) | (F.col("total") < 0),
        "unknown_zone": F.col("pickup_zone").isin(UNKNOWN_ZONES)
        | F.col("dropoff_zone").isin(UNKNOWN_ZONES),
    }


def flagged(trips: DataFrame) -> DataFrame:
    """The trips with a column for each flag, true or false, and `clean`, true when no
    flag is."""
    flags = [
        F.coalesce(rule, F.lit(False)).alias(name) for name, rule in rules().items()
    ]
    with_flags = trips.select("*", *flags)
    return with_flags.withColumn("clean", ~F.greatest(*[F.col(name) for name in FLAGS]))


def flag_counts(flagged: DataFrame) -> dict[str, int]:
    """How many trips each flag marks, and how many are clean."""
    names = [*FLAGS, "clean"]
    row = flagged.agg(*[F.count_if(F.col(name)).alias(name) for name in names]).first()
    return {name: row[name] for name in names}
