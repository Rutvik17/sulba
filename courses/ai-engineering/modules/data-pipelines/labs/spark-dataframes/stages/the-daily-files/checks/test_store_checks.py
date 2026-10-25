from datetime import date

import pytest
from pyspark.sql import functions as F

from flags import flagged
from store import day_folder, load, save
from trips import trips

FIFTH = date(2025, 8, 5)
SIXTH = date(2025, 8, 6)


def counts(spark, folder):
    return {
        row["day"]: row["count"]
        for row in load(spark, folder).groupBy("day").count().collect()
    }


def files(folder):
    """Each file under folder, by its path, with its bytes."""
    return {
        path.relative_to(folder): path.read_bytes()
        for path in folder.rglob("*")
        if path.is_file()
    }


@pytest.mark.id("tst_66tu9r")
def test_saved_again(spark, tmp_path):
    """A day saved again has its trips once"""
    frame = flagged(trips(spark))
    folder = str(tmp_path / "trips")
    save(frame, folder, FIFTH)
    first = counts(spark, folder)
    save(frame, folder, FIFTH)
    assert counts(spark, folder) == first


@pytest.mark.id("tst_ppatpk")
def test_other_days(spark, tmp_path):
    """Saving a day leaves every other day's files as they were"""
    frame = flagged(trips(spark))
    folder = tmp_path / "trips"
    save(frame, str(folder), FIFTH)
    save(frame, str(folder), SIXTH)
    before = files(day_folder(str(folder), FIFTH))
    assert before
    save(frame, str(folder), SIXTH)
    assert files(day_folder(str(folder), FIFTH)) == before
    assert sorted(path.name for path in folder.iterdir()) == [
        "day=2025-08-05",
        "day=2025-08-06",
    ]


@pytest.mark.id("tst_il5e40")
def test_failed_run(spark, tmp_path):
    """A run that fails partway leaves the day's trips as they were"""
    frame = flagged(trips(spark))
    folder = str(tmp_path / "trips")
    save(frame, folder, FIFTH)
    before = counts(spark, folder)
    broken = frame.withColumn(
        "fare",
        F.when(F.col("fare") > 50, F.raise_error(F.lit("broken"))).otherwise(
            F.col("fare")
        ),
    )
    with pytest.raises(Exception):
        save(broken, folder, FIFTH)
    assert counts(spark, folder) == before


@pytest.mark.id("tst_cg64b1")
def test_no_clean_trips(spark, tmp_path):
    """A day with no clean trips has no folder, and loses what was saved for it"""
    frame = flagged(trips(spark))
    folder = str(tmp_path / "trips")
    save(frame, folder, FIFTH)
    save(frame, folder, SIXTH)
    save(frame.withColumn("clean", F.lit(False)), folder, FIFTH)
    assert not day_folder(folder, FIFTH).exists()
    assert list(counts(spark, folder)) == [SIXTH]


@pytest.mark.id("tst_qelkzs")
def test_values(spark, tmp_path):
    """The saved trips are the day's clean trips, value for value"""
    frame = flagged(trips(spark))
    folder = str(tmp_path / "trips")
    save(frame, folder, FIFTH)
    columns = trips(spark).columns
    wanted = frame.where(
        F.col("clean") & (F.to_date("pickup_at") == F.lit(FIFTH))
    ).select(columns)
    saved = load(spark, folder).select(columns)
    assert saved.exceptAll(wanted).count() == 0
    assert wanted.exceptAll(saved).count() == 0
