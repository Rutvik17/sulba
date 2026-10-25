"""Central Park's August 2025 weather, one row a day, from NOAA's daily summaries."""

from pyspark.sql import Column, DataFrame, SparkSession

WEATHER = "data/central-park-2025-08.csv"

# The weather types the file marks with a 1 on the days they were seen.
TYPES = {"fog": "WT01", "thunder": "WT03", "haze": "WT08"}


def attribute(column: str, position: int) -> Column:
    """One of a value's attributes: its measurement flag (0), quality flag (1), source flag (2)
    or time of observation (3), an empty string where it has none."""
    raise NotImplementedError


def measured(column: str) -> Column:
    """A value the file gives in tenths of its unit, as a number of units, missing where it
    failed a quality check."""
    raise NotImplementedError


def weather(spark: SparkSession) -> DataFrame:
    """A row for each day in the file: the day, its rain, whether only a trace fell, its high and
    low, its mean wind, and whether fog, thunder or haze were seen."""
    raise NotImplementedError
