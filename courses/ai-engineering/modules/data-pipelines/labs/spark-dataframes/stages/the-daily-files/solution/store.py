"""Each day's clean trips, saved as Parquet in a folder of their own."""

import shutil
import tempfile
from datetime import date
from pathlib import Path

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F

from flags import FLAGS


def day_folder(folder: str, day: date) -> Path:
    """Where the day's trips are saved: folder/day=YYYY-MM-DD."""
    return Path(folder) / f"day={day.isoformat()}"


def save(flagged: DataFrame, folder: str, day: date) -> None:
    """Saves the day's clean trips, without their flags, in the day's folder, in place of
    what was saved for the day before. The old files go only once the new ones are written
    in full, and a day with no clean trips has no folder."""
    trips = flagged.where(F.col("clean") & (F.to_date("pickup_at") == F.lit(day))).drop(
        *FLAGS, "clean"
    )
    target = day_folder(folder, day)
    target.parent.mkdir(parents=True, exist_ok=True)
    # Written beside the folder, where no reader of it looks, then moved into place.
    staging = Path(tempfile.mkdtemp(dir=target.parent.parent, prefix=".staging-"))
    try:
        written = staging / "trips"
        if not trips.isEmpty():
            trips.write.parquet(str(written))
        if target.exists():
            target.rename(staging / "old")
        if written.exists():
            written.rename(target)
    finally:
        shutil.rmtree(staging, ignore_errors=True)


def load(spark: SparkSession, folder: str) -> DataFrame:
    """Every saved day's trips, with `day`, from its folder's name, as a date."""
    return spark.read.parquet(folder).withColumn("day", F.col("day").cast("date"))
