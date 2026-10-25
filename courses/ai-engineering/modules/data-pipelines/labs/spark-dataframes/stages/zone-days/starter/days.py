"""Each zone's clean pickups day by day, and each borough's busiest zones."""

from pyspark.sql import DataFrame, SparkSession


def zones(spark: SparkSession) -> DataFrame:
    """The city's zones: each one's number, borough and name, missing where the lookup has
    none."""
    raise NotImplementedError


def zone_days(flagged: DataFrame, zones: DataFrame) -> DataFrame:
    """A row for each zone and day with clean pickups: the zone, its borough and name, the day,
    its trips, and `week`, the zone's mean trips a day over the seven days ending that day, a day
    with none counting as 0, from 7 August."""
    raise NotImplementedError


def busiest(zone_days: DataFrame, n: int = 3) -> DataFrame:
    """Each borough's n busiest zones each day by trips, with their place, zones that tie
    sharing one."""
    raise NotImplementedError
