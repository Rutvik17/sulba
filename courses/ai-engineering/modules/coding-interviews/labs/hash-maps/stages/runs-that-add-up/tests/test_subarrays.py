import random

import pytest
from subarrays import count_runs

NUMBERS = 100_000


def every_run(numbers, target):
    """How many runs add up to target, by summing each one."""
    ends = range(len(numbers) + 1)
    return sum(
        1
        for start in ends
        for stop in ends
        if stop > start and sum(numbers[start:stop]) == target
    )


@pytest.mark.id("tst_emk3sl")
def test_runs():
    """Counts the runs that add up"""
    assert count_runs([2, -1, 3, -1, 2], 3) == 3


@pytest.mark.id("tst_p6mdzd")
def test_edges():
    """Counts runs of zeros, and gives 0 for no numbers"""
    assert count_runs([0, 0, 0], 0) == 6
    assert count_runs([5], 5) == 1
    assert count_runs([], 0) == 0


@pytest.mark.id("tst_c0aef4")
def test_every_run():
    """Matches summing every run"""
    rng = random.Random(17)
    for _ in range(300):
        numbers = [rng.randint(-4, 4) for _ in range(rng.randint(0, 12))]
        target = rng.randint(-5, 5)
        assert count_runs(numbers, target) == every_run(numbers, target)


@pytest.mark.id("tst_pj5atw")
def test_long():
    """Counts the runs in a long list in time"""
    # Ones and minus ones in turn: the runs adding up to 1 are those of odd length starting
    # on a one, so there are as many as there are odd lengths that fit after each one.
    numbers = [1, -1] * (NUMBERS // 2)
    expected = sum((NUMBERS - start + 1) // 2 for start in range(0, NUMBERS, 2))
    assert count_runs(numbers, 1) == expected
