import math
import random

import pytest

from promise import chance_by, promised
from schedule import OFFICE, simulate


def counted(finishes, chance):
    """The fewest days within which the share chance of the runs finish, by trying each run's
    finish."""
    return min(
        x for x in finishes if sum(f <= x for f in finishes) >= chance * len(finishes)
    )


def fewest(finishes, chance, x):
    """Whether x is a run's finish within which at least the share chance of the runs finish,
    while fewer finish before it."""
    within = sum(f <= x for f in finishes)
    before = sum(f < x for f in finishes)
    return x in finishes and within >= chance * len(finishes) > before


@pytest.mark.id("tst_4fobp0")
def test_office():
    """Gives the office's 80% days and its chance by day 25"""
    runs = simulate(OFFICE, 10_000, 0)
    assert fewest(runs, 0.8, promised(runs, 0.8))
    assert chance_by(runs, 25) == pytest.approx(sum(run <= 25 for run in runs) / 10_000)


@pytest.mark.id("tst_1jmqi6")
def test_edges():
    """Counts a finish on the day, gives the last run for a chance of 1 and the first for 0"""
    runs = [3.0, 1.0, 2.0, 4.0]
    assert promised(runs, 0.5) == 2.0
    assert promised(runs, 0.51) == 3.0
    assert promised(runs, 1.0) == 4.0
    assert promised(runs, 0.0) == 1.0
    assert chance_by(runs, 2.0) == 0.5
    assert chance_by(runs, 0.5) == 0.0


@pytest.mark.id("tst_lbt6x8")
def test_random():
    """Matches trying each run's finish, on random runs"""
    rng = random.Random(303)
    for _ in range(300):
        runs = [
            rng.choice([rng.uniform(0, 9), float(rng.randint(0, 5))])
            for _ in range(rng.randint(1, 30))
        ]
        chance = rng.choice([rng.random(), 0.5, 0.8, 1.0])
        if chance > 0:
            assert promised(runs, chance) == counted(runs, chance)
        day = rng.uniform(0, 9)
        assert chance_by(runs, day) == pytest.approx(
            sum(run <= day for run in runs) / len(runs)
        )
        assert math.isfinite(chance_by(runs, day))
