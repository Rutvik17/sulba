from datetime import date, datetime, time, timedelta
from decimal import ROUND_HALF_UP, Decimal
from functools import cache

import pandas as pd
import pytest

from payments import by_payment
from trips import PAYMENTS, TRIPS, ZONES, connect, load

CENT = Decimal("0.01")


@cache
def day_trips(day):
    """The trips picked up on day, as the file has them."""
    start = datetime.combine(day, time())
    return pd.read_parquet(
        TRIPS,
        columns=[
            "tpep_pickup_datetime",
            "PULocationID",
            "payment_type",
            "total_amount",
        ],
        filters=[
            ("tpep_pickup_datetime", ">=", start),
            ("tpep_pickup_datetime", "<", start + timedelta(days=1)),
        ],
    )


def cents(amounts):
    """The sum of amounts, each rounded to the cent as the table keeps it."""
    return sum(
        (Decimal(repr(amount)).quantize(CENT, ROUND_HALF_UP) for amount in amounts),
        Decimal("0.00"),
    )


def expected(day):
    """The day's rows, worked out in pandas and Decimal."""
    zones = pd.read_csv(ZONES, keep_default_na=False)
    borough = dict(zip(zones["LocationID"], zones["Borough"], strict=True))
    trips = day_trips(day)
    trips = trips.assign(
        borough=trips["PULocationID"].map(
            lambda zone: None if borough[zone] in ("N/A", "Unknown") else borough[zone]
        )
    )
    names = dict(PAYMENTS)
    rows = []
    known = sorted(trips["borough"].dropna().unique())
    for name in [*known, None]:
        part = (
            trips[trips["borough"].isna()]
            if name is None
            else trips[trips["borough"] == name]
        )
        if part.empty:
            continue
        for code in sorted(part["payment_type"].unique()):
            paid = part[part["payment_type"] == code]
            rows.append(
                ("payment", name, names[code], len(paid), cents(paid["total_amount"]))
            )
        rows.append(("borough", name, None, len(part), cents(part["total_amount"])))
    rows.append(("all", None, None, len(trips), cents(trips["total_amount"])))
    return rows


@pytest.mark.id("tst_3r8dqm")
def test_example(database):
    """5 August by borough and payment, with subtotals"""
    day = date(2025, 8, 5)
    with connect(database) as conn:
        load(conn, [day])
        assert by_payment(conn, day) == expected(day)


@pytest.mark.id("tst_lr1zws")
def test_unknown_borough(database):
    """Trips from a zone with no borough have rows and a subtotal of their own"""
    day = date(2025, 8, 5)
    with connect(database) as conn:
        load(conn, [day])
        rows = by_payment(conn, day)
    unknown = [row for row in rows if row[0] != "all" and row[1] is None]
    assert unknown[-1][0] == "borough"
    assert [row[0] for row in unknown[:-1]] == ["payment"] * (len(unknown) - 1)
    assert unknown[-1][3] == sum(row[3] for row in unknown[:-1]) > 0
    assert rows[-1][:3] == ("all", None, None)


@pytest.mark.id("tst_ohib56")
def test_subtotals_add_up(database):
    """Each borough's payments add up to its subtotal, and the subtotals to the day's"""
    day = date(2025, 8, 10)
    with connect(database) as conn:
        load(conn, [day])
        rows = by_payment(conn, day)
    subtotals = [row for row in rows if row[0] == "borough"]
    for _, borough, _, trips, revenue in subtotals:
        parts = [row for row in rows if row[0] == "payment" and row[1] == borough]
        assert trips == sum(row[3] for row in parts)
        assert revenue == sum(row[4] for row in parts)
    total = rows[-1]
    assert total[3] == sum(row[3] for row in subtotals) == len(day_trips(day))
    assert total[4] == sum(row[4] for row in subtotals)


@pytest.mark.id("tst_e70qbt")
def test_its_own_day(database):
    """With the days either side loaded too, only the day's own trips count"""
    day = date(2025, 8, 16)
    with connect(database) as conn:
        load(conn, [day - timedelta(days=1), day, day + timedelta(days=1)])
        assert by_payment(conn, day) == expected(day)


@pytest.mark.id("tst_6i3dkf")
def test_types(database):
    """Counts come back as whole numbers and takings as exact amounts in cents"""
    day = date(2025, 8, 5)
    with connect(database) as conn:
        load(conn, [day])
        rows = by_payment(conn, day)
    for _, _, _, trips, revenue in rows:
        assert type(trips) is int
        assert type(revenue) is Decimal and revenue == revenue.quantize(CENT)
