import datetime
import math

import pytest

from quote import Quote, quote
from schedule import OFFICE, simulate

MONDAY = datetime.date(2026, 11, 2)


@pytest.mark.id("tst_8n07va")
def test_the_office():
    """Quotes the office's pilot over 10,000 runs"""
    runs = simulate(OFFICE, 10_000, 0)
    days = math.ceil(sorted(runs)[7_999])
    third = days * 140_000 // 3
    assert quote(runs) == Quote(
        days,
        datetime.date(2026, 12, 15),
        days * 140_000,
        {"signed": third + 1, "demo": third, "pilot running": third},
    )


@pytest.mark.id("tst_oz6fnb")
def test_a_short_project():
    """Prices whole days at the day rate, and counts the start as the first day"""
    result = quote(
        [3.2] * 10, MONDAY, day_rate=50_000, milestones={"all": 1}, days_off=frozenset()
    )
    assert result == Quote(4, datetime.date(2026, 11, 5), 200_000, {"all": 200_000})


@pytest.mark.id("tst_0ink37")
def test_thirds():
    """Splits a price into thirds that add up to it"""
    result = quote([1.0], MONDAY, day_rate=100, milestones={"a": 1, "b": 1, "c": 1})
    assert result.payments == {"a": 34, "b": 33, "c": 33}
