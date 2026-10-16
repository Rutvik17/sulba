import random

import pytest
from streaks import longest_streak

NUMBERS = 100_000


def by_sorting(numbers):
    """The longest streak, found by sorting the different numbers and walking them."""
    best = run = 0
    previous = None
    for number in sorted(set(numbers)):
        run = run + 1 if previous is not None and number == previous + 1 else 1
        best = max(best, run)
        previous = number
    return best


@pytest.mark.id("tst_7zwoqa")
def test_streak():
    """Finds the longest streak"""
    assert longest_streak([10, 5, 12, 3, 11, 4, 13, 20]) == 4


@pytest.mark.id("tst_twgph6")
def test_edges():
    """Counts a repeated number once, takes negative numbers, and gives 0 for no numbers"""
    assert longest_streak([1, 2, 2, 3]) == 3
    assert longest_streak([-2, -1, 0, 5]) == 3
    assert longest_streak([7]) == 1
    assert longest_streak([]) == 0


@pytest.mark.id("tst_z0peys")
def test_sorting():
    """Matches sorting the numbers and walking them"""
    rng = random.Random(15)
    for _ in range(300):
        numbers = [rng.randint(-10, 10) for _ in range(rng.randint(0, 14))]
        assert longest_streak(numbers) == by_sorting(numbers)


@pytest.mark.id("tst_jem64k")
def test_long():
    """Finds a long streak in time"""
    rng = random.Random(16)
    numbers = list(range(-NUMBERS // 2, NUMBERS // 2))
    rng.shuffle(numbers)
    assert longest_streak(numbers) == NUMBERS
