import bisect
import random

import pytest
from insertion import insertion_point

NUMBERS = 200_000
SEARCHES = 50_000


@pytest.mark.id("tst_x1zta2")
def test_point():
    """Finds where a value goes"""
    assert insertion_point([1, 3, 3, 7, 9], 3) == 1
    assert insertion_point([1, 3, 3, 7, 9], 8) == 4


@pytest.mark.id("tst_ryg4le")
def test_ends():
    """Puts a value before every number, after every number, or in an empty list"""
    assert insertion_point([1, 3, 7], 0) == 0
    assert insertion_point([1, 3, 7], 9) == 3
    assert insertion_point([], 5) == 0


@pytest.mark.id("tst_3y0asa")
def test_bisect():
    """Matches bisect.bisect_left"""
    rng = random.Random(47)
    for _ in range(300):
        numbers = sorted(rng.randint(-5, 5) for _ in range(rng.randint(0, 10)))
        value = rng.randint(-7, 7)
        assert insertion_point(numbers, value) == bisect.bisect_left(numbers, value)


@pytest.mark.id("tst_oh434c")
def test_long():
    """Searches a long list many times in time"""
    rng = random.Random(48)
    numbers = list(range(0, 2 * NUMBERS, 2))
    values = [rng.randrange(2 * NUMBERS) for _ in range(SEARCHES)]
    # Among the even numbers 0, 2, 4, ..., value goes before the first one not below it.
    assert [insertion_point(numbers, value) for value in values] == [
        (value + 1) // 2 for value in values
    ]
