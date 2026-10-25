import csv
from datetime import date, datetime, timedelta
from functools import cache

import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq
import pytest

from daily import august, boroughs, daily
from flags import flagged
from trips import trips
from weather import weather

FILES = [
    ("data/yellow_tripdata_2025-08.parquet", "tpep"),
    ("data/green_tripdata_2025-08.parquet", "lpep"),
]
DAYS = [date(2025, 8, 1) + timedelta(days=n) for n in range(31)]
COLUMNS = [
    ("day", "date"),
    ("weekday", "string"),
    ("borough", "string"),
    ("trips", "bigint"),
    ("rain_mm", "double"),
    ("trace", "boolean"),
    ("high_c", "double"),
    ("low_c", "double"),
    ("wind_ms", "double"),
    ("fog", "boolean"),
    ("thunder", "boolean"),
    ("haze", "boolean"),
    ("wet", "boolean"),
]
FLAGGED = "pickup_zone int, pickup_at timestamp_ntz, clean boolean"
WEATHER = (
    "day date, rain_mm double, trace boolean, high_c double, low_c double, wind_ms double, "
    "fog boolean, thunder boolean, haze boolean"
)


@cache
def lookup():
    """Each zone's borough from the lookup, None where it has none."""
    with open("data/taxi_zone_lookup.csv", encoding="utf-8", newline="") as file:
        return {
            int(row["LocationID"]): None
            if row["Borough"] in ("N/A", "Unknown")
            else row["Borough"]
            for row in csv.DictReader(file)
        }


@cache
def counts():
    """Each borough's clean pickups on each day, worked out in pyarrow."""
    result = {}
    for path, prefix in FILES:
        table = pq.read_table(path)
        pickup = table[f"{prefix}_pickup_datetime"]
        dropoff = table[f"{prefix}_dropoff_datetime"]
        unknown = pa.array([264, 265])
        flags = [
            pc.or_(
                pc.less(pickup, datetime(2025, 8, 1)),
                pc.greater_equal(pickup, datetime(2025, 9, 1)),
            ),
            pc.less(dropoff, pickup),
            pc.greater(dropoff, pc.add(pickup, pa.scalar(timedelta(hours=24)))),
            pc.less_equal(table["trip_distance"], 0),
            pc.or_(pc.less(table["fare_amount"], 0), pc.less(table["total_amount"], 0)),
            pc.or_(
                pc.is_in(table["PULocationID"], unknown),
                pc.is_in(table["DOLocationID"], unknown),
            ),
        ]
        flag = pc.fill_null(flags[0], False)
        for other in flags[1:]:
            flag = pc.or_(flag, pc.fill_null(other, False))
        clean = table.filter(pc.invert(flag))
        for zone, at in zip(
            clean["PULocationID"].to_pylist(),
            clean[f"{prefix}_pickup_datetime"].to_pylist(),
        ):
            key = (at.date(), lookup()[zone])
            result[key] = result.get(key, 0) + 1
    return result


def rain():
    """Each day's rain in millimetres, from the file."""
    with open("data/central-park-2025-08.csv", encoding="utf-8", newline="") as file:
        return {
            date.fromisoformat(row["DATE"]): int(row["PRCP"]) / 10
            for row in csv.DictReader(file)
        }


@pytest.mark.id("tst_h8x200")
def test_august(spark):
    """Every day of August, once"""
    assert [row["day"] for row in august(spark).collect()] == DAYS


@pytest.mark.id("tst_ygc4hg")
def test_boroughs(spark):
    """Each zone's borough, with none where the lookup has none"""
    result = {row["zone"]: row["borough"] for row in boroughs(spark).collect()}
    assert result == lookup()
    assert boroughs(spark).dtypes == [("zone", "int"), ("borough", "string")]


@pytest.mark.id("tst_v9zubs")
def test_every_borough_and_day(spark):
    """A row for each borough and day, with its clean pickups and the day's weather"""
    result = daily(spark, flagged(trips(spark)), weather(spark))
    assert result.dtypes == COLUMNS
    rows = {(row["day"], row["borough"]): row for row in result.collect()}
    names = {name for name in lookup().values() if name}
    assert rows.keys() == {(day, name) for day in DAYS for name in names}
    assert {key: row["trips"] for key, row in rows.items()} == {
        key: counts().get(key, 0) for key in rows
    }
    for (day, _), row in rows.items():
        assert row["weekday"] == day.strftime("%A")
        assert row["rain_mm"] == pytest.approx(rain()[day])
        assert row["wet"] == (rain()[day] >= 1)


@pytest.mark.id("tst_sa31wq")
def test_days_without_trips_or_weather(spark):
    """A borough with no trips on a day has 0, and a day with no weather keeps its rows"""
    flagged_ = spark.createDataFrame(
        [
            (5, datetime(2025, 8, 5, 9), True),
            (5, datetime(2025, 8, 5, 10), True),
            (5, datetime(2025, 8, 6, 9), False),
            (132, datetime(2025, 8, 6, 9), True),
        ],
        FLAGGED,
    )
    weather_ = spark.createDataFrame(
        [
            (date(2025, 8, 5), 1.0, False, 30.0, 23.3, 3.1, False, True, False),
            (date(2025, 8, 7), 0.0, True, 27.2, 17.8, 1.7, False, False, True),
        ],
        WEATHER,
    )
    rows = {
        (row["day"], row["borough"]): row
        for row in daily(spark, flagged_, weather_).collect()
    }
    assert len(rows) == 31 * 6
    island = rows[date(2025, 8, 5), "Staten Island"]
    assert (island["trips"], island["rain_mm"], island["wet"]) == (2, 1.0, True)
    assert rows[date(2025, 8, 6), "Staten Island"]["trips"] == 0
    assert rows[date(2025, 8, 6), "Queens"]["trips"] == 1
    assert rows[date(2025, 8, 7), "Queens"]["wet"] is False
    for column in ("rain_mm", "trace", "high_c", "wet"):
        assert rows[date(2025, 8, 6), "Manhattan"][column] is None
