from datetime import date, datetime, time, timedelta
from functools import cache

import pandas as pd
import pytest

from hours import hourly
from trips import TRIPS, connect, load


@cache
def day_trips(day):
    """The trips picked up on day, as the file has them."""
    start = datetime.combine(day, time())
    return pd.read_parquet(
        TRIPS,
        columns=["tpep_pickup_datetime", "PULocationID"],
        filters=[
            ("tpep_pickup_datetime", ">=", start),
            ("tpep_pickup_datetime", "<", start + timedelta(days=1)),
        ],
    )


def expected(zone, day):
    """The zone's hours on day, worked out in pandas."""
    trips = day_trips(day)
    hours = trips.loc[trips["PULocationID"] == zone, "tpep_pickup_datetime"].dt.hour
    counts = hours.value_counts().reindex(range(24), fill_value=0).sort_index()
    rolling = counts.rolling(3, min_periods=1).mean()
    change = counts.diff()
    start = datetime.combine(day, time())
    return [
        (
            start + timedelta(hours=hour),
            int(counts[hour]),
            int(counts[: hour + 1].sum()),
            float(rolling[hour]),
            None if hour == 0 else int(change[hour]),
        )
        for hour in range(24)
    ]


def same(rows, wanted):
    assert len(rows) == 24
    for row, want in zip(rows, wanted, strict=True):
        assert row[0] == want[0]
        assert (row[1], row[2]) == (want[1], want[2])
        assert float(row[3]) == pytest.approx(want[3], rel=1e-12)
        assert row[4] == want[4]


@pytest.mark.id("tst_lktswh")
def test_example(database):
    """Midtown Center's hours on 5 August"""
    day = date(2025, 8, 5)
    with connect(database) as conn:
        load(conn, [day])
        same(hourly(conn, 161, day), expected(161, day))


@pytest.mark.id("tst_8h95h3")
def test_empty_hours(database):
    """Hours without a trip come with 0 trips, and count in the means and changes"""
    day = date(2025, 8, 5)
    wanted = expected(255, day)
    assert any(row[1] == 0 for row in wanted)
    with connect(database) as conn:
        load(conn, [day])
        same(hourly(conn, 255, day), wanted)


@pytest.mark.id("tst_ftpt31")
def test_no_trips(database):
    """A zone with no trips that day gives 24 hours of none"""
    day = date(2025, 8, 5)
    start = datetime.combine(day, time())
    with connect(database) as conn:
        load(conn, [day])
        rows = hourly(conn, 103, day)
    assert [(row[0], row[1], row[2], float(row[3])) for row in rows] == [
        (start + timedelta(hours=hour), 0, 0, 0.0) for hour in range(24)
    ]
    assert [row[4] for row in rows] == [None] + [0] * 23


@pytest.mark.id("tst_2thdn6")
def test_its_own_day(database):
    """With the days either side loaded too, only the day's own trips count"""
    day = date(2025, 8, 5)
    with connect(database) as conn:
        load(conn, [day - timedelta(days=1), day, day + timedelta(days=1)])
        for zone in (161, 132, 70):
            same(hourly(conn, zone, day), expected(zone, day))


@pytest.mark.id("tst_skpyez")
def test_types(database):
    """Hours come back as datetimes, counts as whole numbers and means as floats"""
    day = date(2025, 8, 5)
    with connect(database) as conn:
        load(conn, [day])
        rows = hourly(conn, 255, day)
    for hour, trips, running, rolling, change in rows:
        assert type(hour) is datetime
        assert type(trips) is int and type(running) is int
        assert type(rolling) is float
        assert change is None or type(change) is int
