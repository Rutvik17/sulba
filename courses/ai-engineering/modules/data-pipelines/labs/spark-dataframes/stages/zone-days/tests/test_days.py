import csv
from collections import Counter
from datetime import date, datetime, timedelta
from functools import cache

import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq
import pytest

from days import busiest, zone_days, zones
from flags import flagged
from trips import trips

FILES = [
    ("data/yellow_tripdata_2025-08.parquet", "tpep"),
    ("data/green_tripdata_2025-08.parquet", "lpep"),
]
START = datetime(2025, 8, 1)
END = datetime(2025, 9, 1)
FLAGGED = "pickup_zone int, pickup_at timestamp_ntz, clean boolean"


@cache
def lookup():
    """Each zone's borough and name from the lookup, None where it has none."""
    with open("data/taxi_zone_lookup.csv", encoding="utf-8", newline="") as file:
        return {
            int(row["LocationID"]): tuple(
                None if row[key] in ("N/A", "Unknown") else row[key]
                for key in ("Borough", "Zone")
            )
            for row in csv.DictReader(file)
        }


@cache
def counts():
    """Each zone's clean pickups on each day, worked out in pyarrow."""
    result = Counter()
    for path, prefix in FILES:
        table = pq.read_table(path)
        pickup = table[f"{prefix}_pickup_datetime"]
        dropoff = table[f"{prefix}_dropoff_datetime"]
        unknown = pa.array([264, 265])
        flags = [
            pc.or_(pc.less(pickup, START), pc.greater_equal(pickup, END)),
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
            result[zone, at.date()] += 1
    return result


def expected_days():
    """Each zone-day's row, with its week as the mean of the seven days ending on it."""
    rows = {}
    for (zone, day), trips_ in counts().items():
        borough, name = lookup()[zone]
        week = None
        if day >= date(2025, 8, 7):
            week = (
                sum(
                    counts().get((zone, day - timedelta(days=back)), 0)
                    for back in range(7)
                )
                / 7
            )
        rows[zone, day] = (borough, name, trips_, week)
    return rows


@pytest.mark.id("tst_c8w0r5")
def test_zones(spark):
    """Each zone's number, borough and name, with none where the lookup has none"""
    result = {
        row["zone"]: (row["borough"], row["name"]) for row in zones(spark).collect()
    }
    assert result == lookup()
    assert zones(spark).dtypes == [
        ("zone", "int"),
        ("borough", "string"),
        ("name", "string"),
    ]


@pytest.mark.id("tst_p5mcx6")
def test_zone_days(spark):
    """Each zone's clean pickups on each day, and its mean over the seven days ending then"""
    result = zone_days(flagged(trips(spark)), zones(spark))
    assert result.dtypes == [
        ("zone", "int"),
        ("borough", "string"),
        ("name", "string"),
        ("day", "date"),
        ("trips", "bigint"),
        ("week", "double"),
    ]
    rows = {
        (row["zone"], row["day"]): (
            row["borough"],
            row["name"],
            row["trips"],
            row["week"],
        )
        for row in result.collect()
    }
    expected = expected_days()
    assert rows.keys() == expected.keys()
    for key, (borough, name, trips_, week) in expected.items():
        assert rows[key][:3] == (borough, name, trips_), key
        assert rows[key][3] == pytest.approx(week, rel=1e-12), key


@pytest.mark.id("tst_9fnx4m")
def test_days_without_trips(spark):
    """A day with no trips counts as 0 in the week, and the first six days have no week"""
    rows = [
        (161, datetime(2025, 8, day, 9), True)
        for day, trips_ in [(1, 2), (2, 1), (9, 3), (10, 1)]
        for _ in range(trips_)
    ] + [(161, datetime(2025, 8, 3, 9), False)]
    result = zone_days(spark.createDataFrame(rows, FLAGGED), zones(spark))
    weeks = {row["day"].day: (row["trips"], row["week"]) for row in result.collect()}
    assert weeks == {1: (2, None), 2: (1, None), 9: (3, 3 / 7), 10: (1, 4 / 7)}


@pytest.mark.id("tst_3px5k3")
def test_busiest(spark):
    """Each borough's three busiest zones each day, ties kept"""
    result = busiest(zone_days(flagged(trips(spark)), zones(spark)))
    assert [name for name, _ in result.dtypes] == [
        "borough",
        "day",
        "place",
        "zone",
        "name",
        "trips",
    ]
    rows = sorted(
        (row["borough"], row["day"], row["place"], row["zone"], row["trips"])
        for row in result.collect()
    )
    by_day = {}
    for (zone, day), (borough, _, trips_, _) in expected_days().items():
        by_day.setdefault((borough, day), []).append((trips_, zone))
    expected = []
    for (borough, day), zones_ in by_day.items():
        for trips_, zone in zones_:
            place = 1 + sum(other > trips_ for other, _ in zones_)
            if place <= 3:
                expected.append((borough, day, place, zone, trips_))
    assert rows == sorted(expected)


@pytest.mark.id("tst_2l0y1y")
def test_busiest_ties(spark):
    """Zones that tie share a place, and the next place counts them"""
    rows = [
        (zone, datetime(2025, 8, 5, 9), True)
        for zone, trips_ in [(4, 3), (13, 3), (24, 2), (41, 1)]
        for _ in range(trips_)
    ]
    result = busiest(zone_days(spark.createDataFrame(rows, FLAGGED), zones(spark)), n=2)
    places = sorted((row["place"], row["zone"]) for row in result.collect())
    assert places == [(1, 4), (1, 13)]
