import random

import pytest
from warmer import days_until_warmer

DAYS = 100_000


def by_searching(temperatures):
    """Each day's wait, by searching ahead from it."""
    return [
        next(
            (
                later - day
                for later in range(day + 1, len(temperatures))
                if t < temperatures[later]
            ),
            0,
        )
        for day, t in enumerate(temperatures)
    ]


@pytest.mark.id("tst_id1dfd")
def test_warmer():
    """Counts the days until a warmer one"""
    assert days_until_warmer([18, 16, 17, 21, 19, 18, 22]) == [3, 1, 1, 3, 2, 1, 0]


@pytest.mark.id("tst_n0ovoz")
def test_edges():
    """Waits 0 when no warmer day comes, and doesn't count a day as warm"""
    assert days_until_warmer([20, 20, 20]) == [0, 0, 0]
    assert days_until_warmer([25, 20, 15]) == [0, 0, 0]
    assert days_until_warmer([15, 15, 16]) == [2, 1, 0]
    assert days_until_warmer([]) == []


@pytest.mark.id("tst_3342lk")
def test_searching():
    """Matches searching ahead from each day"""
    rng = random.Random(44)
    for _ in range(300):
        temperatures = [rng.randint(10, 15) for _ in range(rng.randint(0, 12))]
        assert days_until_warmer(temperatures) == by_searching(temperatures)


@pytest.mark.id("tst_7hb9lp")
def test_long():
    """Settles a long cooling spell in time"""
    temperatures = list(range(DAYS - 1, 0, -1)) + [DAYS]
    assert days_until_warmer(temperatures) == [
        DAYS - 1 - day for day in range(DAYS - 1)
    ] + [0]
