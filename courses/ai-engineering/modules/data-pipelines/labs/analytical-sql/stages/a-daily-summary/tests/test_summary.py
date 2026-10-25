from datetime import date

import pytest

from summary import refresh
from trips import connect, load

DAY = date(2025, 8, 5)


@pytest.mark.id("tst_ay499c")
def test_a_zone(database):
    """Midtown Center's pickups on 5 August"""
    with connect(database) as conn:
        load(conn, [DAY])
        refresh(conn, DAY)
        row = conn.execute(
            "SELECT pickups FROM daily_zones WHERE day = %s AND zone = 161", (DAY,)
        ).fetchone()
    assert row == (6759,)


@pytest.mark.id("tst_votxer")
def test_written(database):
    """It returns how many zones it wrote"""
    with connect(database) as conn:
        load(conn, [DAY])
        written = refresh(conn, DAY)
        (rows,) = conn.execute(
            "SELECT count(*) FROM daily_zones WHERE day = %s", (DAY,)
        ).fetchone()
    assert written == rows > 0
