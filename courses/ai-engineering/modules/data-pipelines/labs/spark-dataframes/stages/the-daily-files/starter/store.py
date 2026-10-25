"""Each day's clean trips, saved as Parquet in a folder of their own."""

from datetime import date
from pathlib import Path

from pyspark.sql import DataFrame, SparkSession


def day_folder(folder: str, day: date) -> Path:
    """Where the day's trips are saved: folder/day=YYYY-MM-DD."""
    return Path(folder) / f"day={day.isoformat()}"


def save(flagged: DataFrame, folder: str, day: date) -> None:
    """Saves the day's clean trips, without their flags, in the day's folder, in place of
    what was saved for the day before. The old files go only once the new ones are written
    in full, and a day with no clean trips has no folder."""
    raise NotImplementedError


def load(spark: SparkSession, folder: str) -> DataFrame:
    """Every saved day's trips, with `day`, from its folder's name, as a date."""
    raise NotImplementedError
