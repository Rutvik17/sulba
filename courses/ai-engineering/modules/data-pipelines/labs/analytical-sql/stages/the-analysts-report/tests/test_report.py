from datetime import date

import pytest

from report import boroughs
from trips import connect, load

BOROUGHS = {"Bronx", "Brooklyn", "Manhattan", "Queens", "Staten Island"}


@pytest.mark.id("tst_wieh30")
def test_boroughs(database):
    """A row for each of the city's boroughs, and none for Newark"""
    day = date(2025, 8, 5)
    with connect(database) as conn:
        load(conn, [day])
        rows = boroughs(conn, day)
    assert {row[0] for row in rows if row[0] is not None} == BOROUGHS


@pytest.mark.id("tst_94amdh")
def test_shares(database):
    """The shares add up to the whole day"""
    day = date(2025, 8, 5)
    with connect(database) as conn:
        load(conn, [day])
        rows = boroughs(conn, day)
    assert sum(row[3] for row in rows) == pytest.approx(1)


@pytest.mark.id("tst_u4f25j")
def test_manhattan(database):
    """Manhattan has the most trips"""
    day = date(2025, 8, 5)
    with connect(database) as conn:
        load(conn, [day])
        rows = boroughs(conn, day)
    assert max(rows, key=lambda row: row[1])[0] == "Manhattan"
