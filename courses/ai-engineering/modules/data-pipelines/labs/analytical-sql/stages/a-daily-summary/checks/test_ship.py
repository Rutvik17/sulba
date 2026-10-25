from datetime import date, datetime, time, timedelta
from decimal import ROUND_HALF_UP, Decimal

import pandas as pd
import psycopg
import pytest

from summary import refresh
from trips import TRIPS, connect, load

DAY = date(2025, 8, 5)
CENT = Decimal("0.01")


def expected(day):
    """Each zone's row for day, worked out in pandas and Decimal."""
    start = datetime.combine(day, time())
    trips = pd.read_parquet(
        TRIPS,
        columns=[
            "tpep_pickup_datetime",
            "PULocationID",
            "DOLocationID",
            "total_amount",
        ],
        filters=[
            ("tpep_pickup_datetime", ">=", start),
            ("tpep_pickup_datetime", "<", start + timedelta(days=1)),
        ],
    )
    pickups = trips["PULocationID"].value_counts()
    dropoffs = trips["DOLocationID"].value_counts()
    revenue = {}
    for zone, amount in zip(trips["PULocationID"], trips["total_amount"], strict=True):
        cents = Decimal(repr(amount)).quantize(CENT, ROUND_HALF_UP)
        revenue[zone] = revenue.get(zone, Decimal("0.00")) + cents
    zones = sorted(set(pickups.index) | set(dropoffs.index))
    return [
        (
            day,
            int(zone),
            int(pickups.get(zone, 0)),
            int(dropoffs.get(zone, 0)),
            revenue.get(zone, Decimal("0.00")),
        )
        for zone in zones
    ]


def rows(conn, day):
    return conn.execute(
        "SELECT day, zone, pickups, dropoffs, revenue FROM daily_zones "
        "WHERE day = %s ORDER BY zone",
        (day,),
    ).fetchall()


@pytest.mark.id("tst_q2i3gv")
def test_every_zone(database):
    """Every zone of the day, once, with its pickups, drop-offs and takings"""
    with connect(database) as conn:
        load(conn, [DAY, DAY + timedelta(days=1)])
        refresh(conn, DAY)
        assert rows(conn, DAY) == expected(DAY)


@pytest.mark.id("tst_1ryg98")
def test_run_again(database):
    """A run again gives the day's rows as the trips are now"""
    with connect(database) as conn:
        load(conn, [DAY])
        refresh(conn, DAY)
        first = rows(conn, DAY)
        refresh(conn, DAY)
        assert rows(conn, DAY) == first
        conn.execute("DELETE FROM trips WHERE pickup_zone = 161 OR dropoff_zone = 161")
        refresh(conn, DAY)
        again = rows(conn, DAY)
    assert 161 not in {row[1] for row in again}
    assert len(again) == len(first) - 1


@pytest.mark.id("tst_bs7jff")
def test_other_days(database):
    """A day's run leaves the other days' rows as they were"""
    after = DAY + timedelta(days=1)
    with connect(database) as conn:
        load(conn, [DAY, after])
        refresh(conn, DAY)
        refresh(conn, after)
        kept = rows(conn, after)
        refresh(conn, DAY)
        assert rows(conn, after) == kept == expected(after)


@pytest.mark.id("tst_2qqz7o")
def test_all_or_nothing(database):
    """A run that fails partway leaves the day's rows as they were"""
    with connect(database) as conn:
        load(conn, [DAY])
        refresh(conn, DAY)
        before = rows(conn, DAY)
        conn.execute(
            "CREATE FUNCTION refuse() RETURNS trigger LANGUAGE plpgsql "
            "AS $$ BEGIN RAISE EXCEPTION 'the disk is full'; END $$"
        )
        conn.execute(
            "CREATE TRIGGER refuse BEFORE INSERT ON daily_zones "
            "FOR EACH ROW EXECUTE FUNCTION refuse()"
        )
        with pytest.raises(psycopg.Error):
            refresh(conn, DAY)
        assert rows(conn, DAY) == before


@pytest.mark.id("tst_7sauuz")
def test_table(database):
    """The table's columns, their types, and its key"""
    with connect(database) as conn:
        load(conn, [DAY])
        refresh(conn, DAY)
        columns = conn.execute(
            "SELECT attname, format_type(atttypid, atttypmod), attnotnull "
            "FROM pg_attribute WHERE attrelid = 'daily_zones'::regclass "
            "AND attnum > 0 AND NOT attisdropped ORDER BY attnum"
        ).fetchall()
        key = conn.execute(
            "SELECT a.attname FROM pg_index i JOIN pg_attribute a "
            "ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey) "
            "WHERE i.indrelid = 'daily_zones'::regclass AND i.indisprimary "
            "ORDER BY array_position(i.indkey, a.attnum)"
        ).fetchall()
    assert columns == [
        ("day", "date", True),
        ("zone", "integer", True),
        ("pickups", "integer", True),
        ("dropoffs", "integer", True),
        ("revenue", "numeric(12,2)", True),
    ]
    assert key == [("day",), ("zone",)]
