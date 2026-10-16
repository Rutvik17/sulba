import random

import pytest
from shipping import least_capacity

PACKAGES = 50_000
DAYS = 100


def days_needed(weights, capacity):
    """The days a ship of this capacity takes, loading in order."""
    needed, load = 1, 0
    for weight in weights:
        if load + weight > capacity:
            needed, load = needed + 1, 0
        load += weight
    return needed


def by_trying(weights, days):
    """The least capacity, by trying each one from the heaviest package up."""
    capacity = max(weights)
    while days_needed(weights, capacity) > days:
        capacity += 1
    return capacity


@pytest.mark.id("tst_2tz8sk")
def test_capacity():
    """Finds the least capacity that ships in time"""
    assert least_capacity([3, 2, 2, 4, 1, 4], 3) == 6


@pytest.mark.id("tst_wn76qs")
def test_edges():
    """Needs the total weight for one day, and the heaviest package for a day each"""
    assert least_capacity([3, 2, 2, 4, 1, 4], 1) == 16
    assert least_capacity([3, 2, 2, 4, 1, 4], 6) == 4
    assert least_capacity([9, 1, 1], 3) == 9
    assert least_capacity([5], 2) == 5


@pytest.mark.id("tst_f2u36n")
def test_trying():
    """Matches trying each capacity in turn"""
    rng = random.Random(55)
    for _ in range(300):
        weights = [rng.randint(1, 9) for _ in range(rng.randint(1, 10))]
        days = rng.randint(1, len(weights))
        assert least_capacity(weights, days) == by_trying(weights, days)


@pytest.mark.id("tst_5vxlnt")
def test_long():
    """Finds the least capacity for many packages in time"""
    rng = random.Random(54)
    weights = [rng.randint(1, 1000) for _ in range(PACKAGES)]
    capacity = least_capacity(weights, DAYS)
    assert days_needed(weights, capacity) <= DAYS
    assert days_needed(weights, capacity - 1) > DAYS
