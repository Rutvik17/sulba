from datetime import date, datetime, time, timedelta
from functools import cache

import pandas as pd
import pytest

from trips import TRIPS, ZONES, connect, load
from zones import busiest


@cache
def day_trips(day):
    """The trips picked up on day, as the file has them."""
    start = datetime.combine(day, time())
    return pd.read_parquet(
        TRIPS,
        columns=["tpep_pickup_datetime", "PULocationID", "fare_amount"],
        filters=[
            ("tpep_pickup_datetime", ">=", start),
            ("tpep_pickup_datetime", "<", start + timedelta(days=1)),
        ],
    )


def expected(day, n):
    """Each borough's zones ranked n or better on day, worked out in pandas."""
    zones = pd.read_csv(ZONES, keep_default_na=False)
    zones = zones[~zones["Borough"].isin(["N/A", "Unknown"])]
    trips = day_trips(day).merge(zones, left_on="PULocationID", right_on="LocationID")
    counts = (
        trips.groupby(["Borough", "LocationID", "Zone"])
        .agg(trips=("fare_amount", "size"), median_fare=("fare_amount", "median"))
        .reset_index()
    )
    counts["share"] = counts["trips"] / counts.groupby("Borough")["trips"].transform(
        "sum"
    )
    counts["rank"] = (
        counts.groupby("Borough")["trips"]
        .rank(method="min", ascending=False)
        .astype(int)
    )
    kept = counts[counts["rank"] <= n].sort_values(["Borough", "rank", "LocationID"])
    return [
        (
            row.Borough,
            row.LocationID,
            row.Zone,
            row.trips,
            row.share,
            row.median_fare,
            row.rank,
        )
        for row in kept.itertuples()
    ]


def same(rows, wanted):
    assert len(rows) == len(wanted)
    for row, want in zip(rows, wanted, strict=True):
        assert row[:4] == want[:4]
        assert row[4] == pytest.approx(want[4], rel=1e-12)
        assert row[5] == pytest.approx(want[5], abs=1e-9)
        assert row[6] == want[6]


@pytest.mark.id("tst_13yyie")
def test_example(database):
    """Each borough's three busiest zones on 5 August"""
    day = date(2025, 8, 5)
    with connect(database) as conn:
        load(conn, [day])
        same(busiest(conn, day), expected(day, 3))


@pytest.mark.id("tst_varax0")
def test_ties(database):
    """Zones with as many trips share a rank, and the rank after them skips"""
    day = date(2025, 8, 5)
    with connect(database) as conn:
        load(conn, [day])
        rows = busiest(conn, day, 3)
    staten = [(row[1], row[3], row[6]) for row in rows if row[0] == "Staten Island"]
    assert staten == [(6, 2, 1), (23, 2, 1), (187, 1, 3), (214, 1, 3), (251, 1, 3)]


@pytest.mark.id("tst_g04ugl")
def test_every_zone(database):
    """With n above any rank, every zone with a borough and a trip, its share and median"""
    day = date(2025, 8, 5)
    with connect(database) as conn:
        load(conn, [day])
        rows = busiest(conn, day, 300)
    same(rows, expected(day, 300))
    for borough in {row[0] for row in rows}:
        assert sum(row[4] for row in rows if row[0] == borough) == pytest.approx(1)


@pytest.mark.id("tst_p4g048")
def test_other_days(database):
    """Other days, each borough's four busiest zones"""
    days = [date(2025, 8, 10), date(2025, 8, 16)]
    with connect(database) as conn:
        load(conn, days)
        for day in days:
            same(busiest(conn, day, 4), expected(day, 4))


@pytest.mark.id("tst_67eqfb")
def test_its_own_day(database):
    """With the next day's trips loaded too, only the day's own trips count"""
    day = date(2025, 8, 5)
    with connect(database) as conn:
        load(conn, [day, day + timedelta(days=1)])
        same(busiest(conn, day, 300), expected(day, 300))


@pytest.mark.id("tst_fa5u2g")
def test_no_unknown_borough(database):
    """Trips from a zone with no borough are left out, and Newark's are kept"""
    day = date(2025, 8, 5)
    with connect(database) as conn:
        load(conn, [day])
        rows = busiest(conn, day, 300)
    assert all(row[0] is not None for row in rows)
    assert {row[1] for row in rows}.isdisjoint({264, 265})
    assert ("EWR", 1, "Newark Airport") in {row[:3] for row in rows}


@pytest.mark.id("tst_3mdjfc")
def test_types(database):
    """Counts and ranks come back as whole numbers, shares and medians as floats"""
    day = date(2025, 8, 5)
    with connect(database) as conn:
        load(conn, [day])
        rows = busiest(conn, day)
    for borough, zone, name, trips, share, median, rank in rows:
        assert isinstance(borough, str) and isinstance(name, str)
        assert type(zone) is int and type(trips) is int and type(rank) is int
        assert type(share) is float and type(median) is float
