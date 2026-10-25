from datetime import date

import pytest
from pyspark.sql import functions as F

from flags import flagged
from store import day_folder, load, save
from trips import trips

COLUMNS = [
    ("service", "string"),
    ("vendor", "int"),
    ("pickup_at", "timestamp_ntz"),
    ("dropoff_at", "timestamp_ntz"),
    ("passengers", "int"),
    ("distance", "double"),
    ("pickup_zone", "int"),
    ("dropoff_zone", "int"),
    ("payment", "int"),
    ("fare", "double"),
    ("tip", "double"),
    ("total", "double"),
    ("day", "date"),
]


def clean_on(frame, day):
    return frame.where(F.col("clean") & (F.to_date("pickup_at") == F.lit(day))).count()


@pytest.mark.id("tst_ljtu2s")
def test_save_and_load(spark, tmp_path):
    """A saved day loads with its clean trips, its own columns and the day"""
    frame = flagged(trips(spark))
    folder = str(tmp_path / "trips")
    save(frame, folder, date(2025, 8, 5))
    assert day_folder(folder, date(2025, 8, 5)).is_dir()
    saved = load(spark, folder)
    assert saved.dtypes == COLUMNS
    assert saved.count() == clean_on(frame, date(2025, 8, 5))


@pytest.mark.id("tst_005lk0")
def test_two_days(spark, tmp_path):
    """Two saved days load together, each as its own day"""
    frame = flagged(trips(spark))
    folder = str(tmp_path / "trips")
    for day in (date(2025, 8, 5), date(2025, 8, 6)):
        save(frame, folder, day)
    counts = {
        row["day"]: row["count"]
        for row in load(spark, folder).groupBy("day").count().collect()
    }
    assert counts == {
        day: clean_on(frame, day) for day in (date(2025, 8, 5), date(2025, 8, 6))
    }
