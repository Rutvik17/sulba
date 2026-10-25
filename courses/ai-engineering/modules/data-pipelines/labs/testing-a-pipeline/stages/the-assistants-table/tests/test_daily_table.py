import csv
from datetime import date, timedelta

import pytest
from pyspark.sql import functions as F

from daily_table import daily_table

DAYS = [date(2025, 8, 1) + timedelta(days=n) for n in range(31)]


def rain():
    with open("data/central-park-2025-08.csv", encoding="utf-8", newline="") as file:
        return {
            date.fromisoformat(row["DATE"]): int(row["PRCP"]) / 10
            for row in csv.DictReader(file)
        }


@pytest.mark.id("tst_rdi1k5")
def test_columns(spark):
    """The table's columns and their types"""
    assert daily_table(spark).dtypes == [
        ("day", "date"),
        ("weekday", "string"),
        ("borough", "string"),
        ("trips", "bigint"),
        ("rain_mm", "double"),
        ("high_c", "double"),
        ("wet", "boolean"),
    ]


@pytest.mark.id("tst_mif2cb")
def test_every_day(spark):
    """Every day of August, with trips in Manhattan"""
    rows = daily_table(spark).where(F.col("borough") == "Manhattan").collect()
    assert sorted(row["day"] for row in rows) == DAYS
    assert all(row["trips"] > 0 for row in rows)


@pytest.mark.id("tst_sy9k65")
def test_wet_days(spark):
    """The wet days are the days with 1 mm of rain or more"""
    wet = {row["day"] for row in daily_table(spark).where("wet").collect()}
    assert wet == {day for day, mm in rain().items() if mm >= 1}
