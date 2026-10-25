"""Flags for the trips whose records can't be taken at their word."""

from pyspark.sql import DataFrame

FLAGS = [
    "outside_month",
    "backwards",
    "too_long",
    "no_distance",
    "negative",
    "unknown_zone",
]


def flagged(trips: DataFrame) -> DataFrame:
    """The trips with a column for each flag, true or false, and `clean`, true when no
    flag is."""
    raise NotImplementedError


def flag_counts(flagged: DataFrame) -> dict[str, int]:
    """How many trips each flag marks, and how many are clean."""
    raise NotImplementedError
