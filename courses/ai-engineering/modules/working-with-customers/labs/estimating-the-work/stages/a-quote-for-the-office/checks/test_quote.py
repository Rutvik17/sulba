import datetime
import math
import random
from fractions import Fraction

import pytest

from promise import promised
from quote import DAYS_OFF, quote


@pytest.mark.id("tst_cq5n24")
def test_whole_days():
    """The fewest whole days by which four runs in five finish"""
    assert quote([28.0] * 5).days == 28
    assert quote([27.01] * 5).days == 28
    assert quote([27.4] * 5).days == 28
    rng = random.Random(311)
    for _ in range(200):
        runs = [rng.uniform(1, 60) for _ in range(rng.randint(1, 40))]
        assert quote(runs).days == math.ceil(promised(runs, 0.8))


def done_by(start, days, days_off=frozenset()):
    return quote([float(days)], start, milestones={"all": 1}, days_off=days_off).done_by


@pytest.mark.id("tst_dl0yye")
def test_working_days():
    """Counts working days from the start, past weekends and days off"""
    friday, saturday = datetime.date(2026, 11, 6), datetime.date(2026, 11, 7)
    monday = datetime.date(2026, 11, 9)
    assert done_by(monday, 1) == monday
    assert done_by(friday, 1) == friday
    assert done_by(friday, 2) == monday
    assert done_by(saturday, 1) == monday
    assert done_by(saturday, 6) == datetime.date(2026, 11, 16)
    wednesday = datetime.date(2026, 11, 11)
    assert done_by(monday, 3, frozenset({wednesday})) == datetime.date(2026, 11, 12)
    assert done_by(wednesday, 1, frozenset({wednesday})) == datetime.date(2026, 11, 12)
    off = frozenset({monday, datetime.date(2026, 11, 10)})
    assert done_by(saturday, 1, off) == wednesday
    november = datetime.date(2026, 11, 2)
    assert done_by(november, 29, DAYS_OFF) == datetime.date(2026, 12, 15)


def largest_remainders(price, milestones):
    total = sum(milestones.values())
    exact = {name: Fraction(price * share, total) for name, share in milestones.items()}
    paid = {name: int(value) for name, value in exact.items()}
    order = sorted(
        enumerate(milestones),
        key=lambda item: (-(exact[item[1]] - paid[item[1]]), item[0]),
    )
    for _, name in order[: price - sum(paid.values())]:
        paid[name] += 1
    return paid


@pytest.mark.id("tst_yoc7o3")
def test_payments_to_the_cent():
    """Payments add up to the price, each within a cent of its share"""
    rng = random.Random(312)
    for _ in range(300):
        names = [f"m{place}" for place in range(rng.randint(1, 6))]
        milestones = {name: rng.randint(1, 9) for name in names}
        price = rng.randint(1, 5_000_000)
        payments = quote([1.0], day_rate=price, milestones=milestones).payments
        assert list(payments) == names
        assert sum(payments.values()) == price
        assert payments == largest_remainders(price, milestones)
    sevenths = quote([1.0], day_rate=100, milestones={"a": 1, "b": 2, "c": 4}).payments
    assert sevenths == {"a": 14, "b": 29, "c": 57}


@pytest.mark.id("tst_ku9y5h")
def test_a_quote_it_cant_price():
    """Refuses no runs, a day rate of 0 or less, and shares of 0 or less"""
    for finishes, day_rate, milestones in [
        ([], 140_000, {"all": 1}),
        ([3.0], 0, {"all": 1}),
        ([3.0], -100, {"all": 1}),
        ([3.0], 140_000, {}),
        ([3.0], 140_000, {"signed": 1, "demo": 0}),
        ([3.0], 140_000, {"signed": 2, "demo": -1}),
    ]:
        with pytest.raises(ValueError):
            quote(finishes, day_rate=day_rate, milestones=milestones)
