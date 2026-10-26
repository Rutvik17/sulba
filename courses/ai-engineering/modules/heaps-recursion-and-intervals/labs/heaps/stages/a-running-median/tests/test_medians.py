import random
import statistics

import pytest

from medians import medians

NUMBERS = 200_000


@pytest.mark.id("tst_o1te3m")
def test_medians():
    """Gives the median after each number"""
    assert medians([5, 15, 1, 3]) == [5.0, 10.0, 5.0, 4.0]


@pytest.mark.id("tst_6gasm8")
def test_edges():
    """Handles no numbers, repeats, negative numbers and numbers in order"""
    assert medians([]) == []
    assert medians([2, 2, 2]) == [2.0, 2.0, 2.0]
    assert medians([-3, -1]) == [-3.0, -2.0]
    assert medians([1, 2, 3, 4]) == [1.0, 1.5, 2.0, 2.5]
    assert medians([4, 3, 2, 1]) == [4.0, 3.5, 3.0, 2.5]


@pytest.mark.id("tst_xqshrm")
def test_random():
    """Matches the median of each prefix, on random numbers"""
    rng = random.Random(211)
    for _ in range(200):
        numbers = [rng.randint(-50, 50) for _ in range(rng.randint(1, 40))]
        expected = [
            float(statistics.median(numbers[: n + 1])) for n in range(len(numbers))
        ]
        assert medians(numbers) == expected


@pytest.mark.id("tst_oyiq4o")
def test_long():
    """Gives the medians of a long stream in time"""
    rng = random.Random(212)
    numbers = [rng.randint(-1_000_000, 1_000_000) for _ in range(NUMBERS)]
    found = medians(numbers)
    assert len(found) == NUMBERS
    assert found[-1] == float(statistics.median(numbers))
