"""Each borough's clean pickups on each day of August, with the day's weather."""

from pyspark.sql import DataFrame, SparkSession

ZONES = "data/taxi_zone_lookup.csv"

# What the zone lookup writes where it has no borough.
MISSING = ["N/A", "Unknown"]

# Rain from which a day counts as wet, in millimetres.
WET_MM = 1.0


def august(spark: SparkSession) -> DataFrame:
    """Every day of August 2025, one row each, in `day`."""
    raise NotImplementedError


def boroughs(spark: SparkSession) -> DataFrame:
    """Each zone's number and borough, the borough missing where the lookup has none."""
    raise NotImplementedError


def daily(spark: SparkSession, flagged: DataFrame, weather: DataFrame) -> DataFrame:
    """A row for each day of August and each borough: the day, its weekday, the borough, its
    clean pickups that day, the day's weather, and whether it was wet. A borough with no
    clean pickups on a day has 0 of them, and a day the weather lacks has no weather."""
    raise NotImplementedError
