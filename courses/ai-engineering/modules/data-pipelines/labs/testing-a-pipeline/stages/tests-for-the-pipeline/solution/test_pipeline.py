"""Tests for the pipeline: the weather, the daily table and the wet days against dry ones."""

from datetime import date, datetime

import pytest

import weather as weather_file
from daily import daily
from rain import against_dry_days
from weather import weather

HEADER = (
    "STATION,DATE,AWND,AWND_ATTRIBUTES,PRCP,PRCP_ATTRIBUTES,SNOW,SNOW_ATTRIBUTES,TMAX,"
    "TMAX_ATTRIBUTES,TMIN,TMIN_ATTRIBUTES,WT01,WT01_ATTRIBUTES,WT03,WT03_ATTRIBUTES,WT08,"
    "WT08_ATTRIBUTES"
)
FLAGGED = "pickup_zone int, pickup_at timestamp_ntz, clean boolean"
WEATHER = (
    "day date, rain_mm double, trace boolean, high_c double, low_c double, wind_ms double, "
    "fog boolean, thunder boolean, haze boolean"
)
DAILY = "day date, weekday string, borough string, trips bigint, rain_mm double, wet boolean"


def day_line(day, rain="    0", rain_flags=",,W,2400", high="  300", high_flags=",,W"):
    """One day of the weather file, in the service's layout, with a low of 20.0 and wind of 2.0."""
    return (
        f'"USW00094728","{day}","   20",",,W","{rain}","{rain_flags}","    0",",,W,2400",'
        f'"{high}","{high_flags}","  200",",,W",,,,,,'
    )


@pytest.fixture
def weather_file_of(tmp_path, monkeypatch):
    """Points weather.py at a file of the given days."""

    def write(*lines):
        path = tmp_path / "weather.csv"
        path.write_text("\n".join([HEADER, *lines]) + "\n", encoding="utf-8")
        monkeypatch.setattr(weather_file, "WEATHER", str(path))

    return write


def weather_of(spark, *days):
    """A weather table of the given days, each (day, rain), dry and mild otherwise."""
    rows = [
        (day, rain, False, 30.0, 20.0, 2.0, False, False, False) for day, rain in days
    ]
    return spark.createDataFrame(rows, WEATHER)


def trips_of(spark, *trips):
    """Flagged trips, each (zone, pickup time), all clean."""
    return spark.createDataFrame([(zone, at, True) for zone, at in trips], FLAGGED)


def test_weather_in_units(spark, weather_file_of):
    weather_file_of(day_line("2025-08-13", rain="  180", high="  317"))
    (row,) = weather(spark).collect()
    assert (
        row["rain_mm"],
        row["high_c"],
        row["low_c"],
        row["wind_ms"],
    ) == pytest.approx((18.0, 31.7, 20.0, 2.0))


def test_weather_leaves_out_a_failed_value(spark, weather_file_of):
    weather_file_of(
        day_line("2025-08-13", rain="  180", high="  999", high_flags=",X,W")
    )
    (row,) = weather(spark).collect()
    assert row["high_c"] is None
    assert row["rain_mm"] == pytest.approx(18.0)


def test_weather_trace(spark, weather_file_of):
    weather_file_of(day_line("2025-08-01", rain_flags="T,,W,2400"))
    (row,) = weather(spark).collect()
    assert (row["rain_mm"], row["trace"]) == (0.0, True)


def test_daily_keeps_a_borough_without_trips(spark):
    trips = trips_of(spark, (132, datetime(2025, 8, 5, 9)))
    rows = daily(spark, trips, weather_of(spark, (date(2025, 8, 5), 0.0))).collect()
    assert len(rows) == 31 * 6
    found = {(row["day"], row["borough"]): row["trips"] for row in rows}
    assert found[date(2025, 8, 5), "Queens"] == 1
    assert found[date(2025, 8, 5), "Staten Island"] == 0


def test_daily_weekdays(spark):
    rows = daily(spark, trips_of(spark), weather_of(spark)).collect()
    for row in rows:
        assert row["weekday"] == row["day"].strftime("%A")
    assert {row["weekday"] for row in rows if row["day"] == date(2025, 8, 1)} == {
        "Friday"
    }


def test_daily_wet_from_1_mm(spark):
    weather_ = weather_of(spark, (date(2025, 8, 5), 1.0), (date(2025, 8, 6), 0.9))
    rows = daily(spark, trips_of(spark), weather_).where("borough = 'Queens'").collect()
    wet = {row["day"]: row["wet"] for row in rows}
    assert (wet[date(2025, 8, 5)], wet[date(2025, 8, 6)], wet[date(2025, 8, 7)]) == (
        True,
        False,
        None,
    )


def test_against_dry_days_of_the_same_weekday(spark):
    table = spark.createDataFrame(
        [
            (date(2025, 8, 13), "Wednesday", "Queens", 120, 18.0, True),
            (date(2025, 8, 27), "Wednesday", "Queens", 100, 0.0, False),
            (date(2025, 8, 14), "Thursday", "Queens", 300, 0.0, False),
        ],
        DAILY,
    )
    (row,) = against_dry_days(table).collect()
    assert (row["day"], row["dry_days"], row["dry_trips"]) == (
        date(2025, 8, 13),
        1,
        100.0,
    )
    assert row["change"] == pytest.approx(0.2)
