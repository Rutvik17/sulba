from datetime import date, datetime, time, timedelta

import pandas as pd
import pytest

from report import boroughs
from trips import TRIPS, ZONES, connect, load

DAY = date(2025, 8, 5)


def expected():
    """Each known borough's trips and passengers per trip on DAY, worked out in pandas."""
    start = datetime.combine(DAY, time())
    trips = pd.read_parquet(
        TRIPS,
        columns=["tpep_pickup_datetime", "PULocationID", "passenger_count"],
        filters=[
            ("tpep_pickup_datetime", ">=", start),
            ("tpep_pickup_datetime", "<", start + timedelta(days=1)),
        ],
    )
    zones = pd.read_csv(ZONES, keep_default_na=False)
    known = zones[~zones["Borough"].isin(["N/A", "Unknown", "EWR"])]
    trips = trips.merge(known, left_on="PULocationID", right_on="LocationID")
    grouped = trips.groupby("Borough")["passenger_count"]
    return {
        borough: (int(size), float(mean))
        for borough, size, mean in zip(
            grouped.size().index, grouped.size(), grouped.mean(), strict=True
        )
    }


@pytest.mark.id("tst_vt3fsr")
def test_every_trip_but_newarks(database):
    """Trips from zones with no borough have their row, and Newark's none"""
    with connect(database) as conn:
        load(conn, [DAY])
        rows = boroughs(conn, DAY)
    names = [row[0] for row in rows]
    assert None in names
    assert "EWR" not in names


@pytest.mark.id("tst_f4efoy")
def test_trips_without_passengers(database):
    """Trips that report no passengers count as trips"""
    wanted = expected()
    with connect(database) as conn:
        load(conn, [DAY])
        rows = {row[0]: row for row in boroughs(conn, DAY) if row[0] is not None}
    assert {borough: row[1] for borough, row in rows.items()} == {
        borough: trips for borough, (trips, _) in wanted.items()
    }


@pytest.mark.id("tst_o4bys6")
def test_passengers_per_trip(database):
    """Passengers per trip, over the trips that report them"""
    wanted = expected()
    with connect(database) as conn:
        load(conn, [DAY])
        rows = {row[0]: row for row in boroughs(conn, DAY) if row[0] is not None}
    for borough, (_, passengers) in wanted.items():
        assert rows[borough][2] == pytest.approx(passengers, rel=1e-12)


@pytest.mark.id("tst_6wtj0t")
def test_only_the_days_trips(database):
    """Trips picked up at the next midnight belong to the next day's report"""
    midnight = datetime.combine(DAY + timedelta(days=1), time())
    with connect(database) as conn:
        load(conn, [DAY])
        before = boroughs(conn, DAY)
        for _ in range(4):
            conn.execute(
                "INSERT INTO trips (pickup_at, dropoff_at, passengers, pickup_zone, "
                "dropoff_zone, payment, fare, total) "
                "VALUES (%s, %s, 2, 161, 237, 1, 12.10, 19.85)",
                (midnight, midnight + timedelta(minutes=12)),
            )
        assert boroughs(conn, DAY) == before
