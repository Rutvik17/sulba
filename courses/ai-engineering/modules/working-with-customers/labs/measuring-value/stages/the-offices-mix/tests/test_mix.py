import csv
import math
import random

import pytest

from kinds import Share, by_kind
from mix import OFFICE, Estimate, weighted


def read():
    with open("data/runs.csv", encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


@pytest.mark.id("tst_fzoau3")
def test_the_office():
    """Weights each kind by the office's contacts"""
    shares = by_kind(read(), "agent")
    estimate = weighted(shares, OFFICE)
    total = sum(OFFICE.values())
    value = sum(count / total * shares[kind].value for kind, count in OFFICE.items())
    error = math.sqrt(
        sum((count / total * shares[kind].error) ** 2 for kind, count in OFFICE.items())
    )
    assert estimate.value == pytest.approx(value)
    assert estimate.high - estimate.value == pytest.approx(1.959964 * error, rel=1e-6)
    assert estimate.value - estimate.low == pytest.approx(1.959964 * error, rel=1e-6)


@pytest.mark.id("tst_fsd8eg")
def test_one_kind():
    """Gives one kind's share and interval when all the contacts are of that kind"""
    shares = {"case": Share(0.6, 0.05, 20), "new": Share(0.9, 0.02, 20)}
    estimate = weighted(shares, {"case": 500, "new": 0}, confidence=0.9)
    assert estimate.value == pytest.approx(0.6)
    assert estimate.high == pytest.approx(0.6 + 1.644854 * 0.05, rel=1e-6)


@pytest.mark.id("tst_713t6t")
def test_within_0_and_1():
    """Keeps the interval within 0 and 1"""
    shares = {"vague": Share(0.98, 0.04, 20), "case": Share(0.03, 0.04, 20)}
    assert weighted(shares, {"vague": 1}) == Estimate(
        pytest.approx(0.98), pytest.approx(0.98 - 1.959964 * 0.04, rel=1e-6), 1.0
    )
    assert weighted(shares, {"case": 1}).low == 0.0
    rng = random.Random(202)
    for _ in range(200):
        shares = {kind: Share(rng.random(), rng.uniform(0, 0.3), 20) for kind in "abc"}
        volumes = {kind: rng.randint(0, 50) for kind in "abc"}
        volumes["a"] += 1
        estimate = weighted(shares, volumes)
        assert 0 <= estimate.low <= estimate.value <= estimate.high <= 1


@pytest.mark.id("tst_uzv1rb")
def test_what_it_cant_weigh():
    """Refuses a kind without a share, and no contacts"""
    shares = {"case": Share(0.6, 0.05, 20)}
    with pytest.raises(ValueError):
        weighted(shares, {"case": 10, "new": 5})
    with pytest.raises(ValueError):
        weighted(shares, {"case": 0})
