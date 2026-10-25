import random

import pytest

from inversions import inversions

NUMBERS = 100_000


def every_pair(numbers):
    """How many inversions, by checking every pair of places."""
    return sum(
        1
        for i in range(len(numbers))
        for j in range(i + 1, len(numbers))
        if numbers[i] > numbers[j]
    )


@pytest.mark.id("tst_vto6yr")
def test_inversions():
    """Counts a list's inversions"""
    assert inversions([2, 4, 1, 3, 5]) == 3


@pytest.mark.id("tst_q8xap8")
def test_edges():
    """Counts none for no numbers, one, equal numbers and numbers in order"""
    assert inversions([]) == 0
    assert inversions([7]) == 0
    assert inversions([4, 4, 4]) == 0
    assert inversions([1, 2, 3]) == 0
    assert inversions([3, 2, 1]) == 3
    assert inversions([0, -1, -2, 5]) == 3


@pytest.mark.id("tst_89o2pe")
def test_random():
    """Matches checking every pair, on random lists"""
    rng = random.Random(341)
    for _ in range(300):
        numbers = [rng.randint(0, 6) for _ in range(rng.randint(0, 15))]
        assert inversions(numbers) == every_pair(numbers)


@pytest.mark.id("tst_720vqt")
def test_long():
    """Counts the inversions of long lists in time"""
    assert inversions(list(range(NUMBERS, 0, -1))) == NUMBERS * (NUMBERS - 1) // 2
    half = NUMBERS // 3
    assert inversions(list(range(half, NUMBERS)) + list(range(half))) == half * (
        NUMBERS - half
    )
