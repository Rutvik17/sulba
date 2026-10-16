import random

import pytest
from runs import largest_run

NUMBERS = 100_000


def every_run(numbers):
    """The largest sum of every run."""
    ends = range(len(numbers) + 1)
    return max(
        sum(numbers[start:stop]) for start in ends for stop in ends if stop > start
    )


@pytest.mark.id("tst_5zlkp4")
def test_run():
    """Finds the largest run"""
    assert largest_run([2, -5, 4, -1, 3, -6, 2]) == 6


@pytest.mark.id("tst_5gxg3t")
def test_negative():
    """Gives the largest number when every number is negative"""
    assert largest_run([-3, -1, -2]) == -1
    assert largest_run([-7]) == -7


@pytest.mark.id("tst_meqfkp")
def test_every_run():
    """Matches the largest sum of every run"""
    rng = random.Random(5)
    for _ in range(300):
        numbers = [rng.randint(-20, 20) for _ in range(rng.randint(1, 12))]
        assert largest_run(numbers) == every_run(numbers)


@pytest.mark.id("tst_dgojpg")
def test_long():
    """Finds the largest run in a long list in time"""
    rng = random.Random(6)
    numbers = [-rng.randint(1, 3) for _ in range(NUMBERS)]
    # Two runs of 20 with a gap of -3 between them: together they make 37.
    numbers[50_000:50_013] = [4] * 5 + [-1] * 3 + [4] * 5
    assert largest_run(numbers) == 37
