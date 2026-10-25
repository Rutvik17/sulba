"""Each borough's trips on wet days against its trips on dry days."""

from pyspark.sql import DataFrame


def wet_and_dry(daily: DataFrame) -> DataFrame:
    """Each borough's wet and dry days: how many of each, and its mean clean pickups on them. A
    day without weather is neither."""
    raise NotImplementedError


def against_dry_days(daily: DataFrame) -> DataFrame:
    """Each borough's wet days, each with the borough's dry days of the same weekday: how many
    there were, their mean clean pickups, and the wet day's change from that mean."""
    raise NotImplementedError
