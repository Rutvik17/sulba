import random

import pytest
from reach import shortest_reach

NUMBERS = 100_000


def every_run(numbers, target):
    """The shortest run reaching target, or 0, by summing every run."""
    lengths = [
        stop - start
        for start in range(len(numbers))
        for stop in range(start + 1, len(numbers) + 1)
        if sum(numbers[start:stop]) >= target
    ]
    return min(lengths, default=0)


@pytest.mark.id("tst_39i924")
def test_reach():
    """Finds the shortest run that reaches the target"""
    assert shortest_reach([2, 1, 5, 2, 3, 2], 7) == 2


@pytest.mark.id("tst_3buf8j")
def test_edges():
    """Gives 0 when no run reaches it, and handles one number or all of them"""
    assert shortest_reach([1, 1, 1], 5) == 0
    assert shortest_reach([], 1) == 0
    assert shortest_reach([1, 9, 1], 9) == 1
    assert shortest_reach([2, 2, 2], 6) == 3


@pytest.mark.id("tst_l0j1ld")
def test_every_run():
    """Matches summing every run"""
    rng = random.Random(37)
    for _ in range(300):
        numbers = [rng.randint(1, 9) for _ in range(rng.randint(0, 12))]
        target = rng.randint(1, 40)
        assert shortest_reach(numbers, target) == every_run(numbers, target)


@pytest.mark.id("tst_5vxn7e")
def test_long():
    """Finds the shortest run in a long list in time"""
    rng = random.Random(38)
    numbers = [rng.randint(1, 10) for _ in range(NUMBERS)]
    numbers[60_000:60_003] = [5000, 5000, 5000]
    assert shortest_reach(numbers, 15_000) == 3
    assert shortest_reach(numbers, 10 * NUMBERS + 15_000) == 0
