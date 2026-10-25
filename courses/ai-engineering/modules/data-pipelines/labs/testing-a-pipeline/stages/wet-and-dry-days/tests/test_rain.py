from datetime import date

import pytest

from daily import daily
from flags import flagged
from rain import against_dry_days, wet_and_dry
from trips import trips
from weather import weather

DAILY = "day date, weekday string, borough string, trips bigint, rain_mm double, wet boolean"

# Two boroughs' days: Wednesdays and Thursdays, wet, dry and without weather.
ROWS = [
    (date(2025, 8, 6), "Wednesday", "Queens", 90, 1.5, True),
    (date(2025, 8, 13), "Wednesday", "Queens", 120, 18.0, True),
    (date(2025, 8, 20), "Wednesday", "Queens", 80, 0.0, False),
    (date(2025, 8, 27), "Wednesday", "Queens", 120, 0.0, False),
    (date(2025, 8, 7), "Thursday", "Queens", 50, None, None),
    (date(2025, 8, 21), "Thursday", "Queens", 70, 6.9, True),
    (date(2025, 8, 6), "Wednesday", "Bronx", 3, 1.5, True),
    (date(2025, 8, 27), "Wednesday", "Bronx", 0, 0.0, False),
]


@pytest.mark.id("tst_g2ns0c")
def test_wet_and_dry(spark):
    """Each borough's wet and dry days, and its mean trips on each"""
    result = wet_and_dry(spark.createDataFrame(ROWS, DAILY))
    assert result.dtypes == [
        ("borough", "string"),
        ("wet_days", "bigint"),
        ("wet_trips", "double"),
        ("dry_days", "bigint"),
        ("dry_trips", "double"),
    ]
    rows = {row["borough"]: tuple(row)[1:] for row in result.collect()}
    assert rows == {"Queens": (3, 280 / 3, 2, 100.0), "Bronx": (1, 3.0, 1, 0.0)}


@pytest.mark.id("tst_mxtmny")
def test_against_dry_days(spark):
    """Each wet day against the borough's dry days of the same weekday"""
    result = against_dry_days(spark.createDataFrame(ROWS, DAILY))
    assert result.dtypes == [
        ("borough", "string"),
        ("day", "date"),
        ("weekday", "string"),
        ("rain_mm", "double"),
        ("trips", "bigint"),
        ("dry_days", "bigint"),
        ("dry_trips", "double"),
        ("change", "double"),
    ]
    rows = {
        (row["borough"], row["day"].day): tuple(row)[5:] for row in result.collect()
    }
    assert rows == {
        ("Queens", 6): (2, 100.0, pytest.approx(-0.1)),
        ("Queens", 13): (2, 100.0, pytest.approx(0.2)),
        ("Queens", 21): (0, None, None),
        ("Bronx", 6): (1, 0.0, None),
    }


@pytest.mark.id("tst_6bbw1e")
def test_august(spark):
    """August's wet days in every borough, against dry days of the same weekday"""
    table = daily(spark, flagged(trips(spark)), weather(spark)).cache()
    days = {
        (row["borough"], row["day"]): (row["weekday"], row["trips"], row["wet"])
        for row in table.collect()
    }
    rows = against_dry_days(table).collect()
    assert {(row["borough"], row["day"]) for row in rows} == {
        key for key, (_, _, wet) in days.items() if wet
    }
    for row in rows:
        weekday = days[row["borough"], row["day"]][0]
        dry = [
            trips_
            for (borough, _), (other, trips_, wet) in days.items()
            if borough == row["borough"] and other == weekday and wet is False
        ]
        assert row["dry_days"] == len(dry)
        assert row["dry_trips"] == pytest.approx(sum(dry) / len(dry))
        assert row["change"] == pytest.approx(row["trips"] / (sum(dry) / len(dry)) - 1)
    table.unpersist()
