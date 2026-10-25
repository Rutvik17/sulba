import csv
from datetime import date, datetime, timedelta
from functools import cache

import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq
import pytest

from daily_table import daily_table

FILES = [
    ("data/yellow_tripdata_2025-08.parquet", "tpep"),
    ("data/green_tripdata_2025-08.parquet", "lpep"),
]
DAYS = [date(2025, 8, 1) + timedelta(days=n) for n in range(31)]


@cache
def boroughs():
    """Each zone's borough, as the lookup writes it."""
    with open("data/taxi_zone_lookup.csv", encoding="utf-8", newline="") as file:
        return {int(row["LocationID"]): row["Borough"] for row in csv.DictReader(file)}


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
        days = pc.cast(clean[f"{prefix}_pickup_datetime"], pa.date32()).to_pylist()
        for zone, day in zip(clean["PULocationID"].to_pylist(), days):
            key = (day, boroughs()[zone])
            result[key] = result.get(key, 0) + 1
    return result


def traces():
    """The days on which only a trace of rain fell, from the file."""
    with open("data/central-park-2025-08.csv", encoding="utf-8", newline="") as file:
        return {
            date.fromisoformat(row["DATE"])
            for row in csv.DictReader(file)
            if row["PRCP_ATTRIBUTES"].split(",")[0] == "T"
        }


@pytest.fixture(scope="module")
def rows(spark_session):
    """The table's rows, by day and borough."""
    return {
        (row["day"], row["borough"]): row
        for row in daily_table(spark_session).collect()
    }


@pytest.mark.id("tst_jy9ecx")
def test_traces(rows):
    """A day with a trace of rain had 0 mm and was dry"""
    for (day, _), row in rows.items():
        if day in traces():
            assert (row["rain_mm"], row["wet"]) == (0.0, False)


@pytest.mark.id("tst_dzdg4x")
def test_every_trip(rows):
    """Each borough's count holds every clean pickup that day"""
    for key, row in rows.items():
        assert row["trips"] == counts().get(key, 0)


@pytest.mark.id("tst_o5x2ri")
def test_weekdays(rows):
    """Each day has its weekday"""
    for (day, _), row in rows.items():
        assert row["weekday"] == day.strftime("%A")


@pytest.mark.id("tst_dwftiw")
def test_every_borough_every_day(rows):
    """Every borough has a row on every day, with 0 trips on a day it had none"""
    names = set(boroughs().values()) - {"N/A", "Unknown"}
    assert rows.keys() == {(day, name) for day in DAYS for name in names}
    assert rows[date(2025, 8, 5), "Staten Island"]["trips"] == 0
