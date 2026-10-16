import bisect
import random

import pytest
from first_last import first_and_last

NUMBERS = 200_000
RUN = 50_000
SEARCHES = 50_000


def by_bisect(numbers, value):
    """The first and last positions, from bisect_left and bisect_right."""
    first, past = (
        bisect.bisect_left(numbers, value),
        bisect.bisect_right(numbers, value),
    )
    return (first, past - 1) if first < past else None


@pytest.mark.id("tst_gjcbxt")
def test_run():
    """Finds the first and last positions of a value"""
    assert first_and_last([2, 4, 4, 4, 6, 8], 4) == (1, 3)


@pytest.mark.id("tst_75uhhz")
def test_edges():
    """Gives None for a missing value, and handles one copy, all copies and no numbers"""
    assert first_and_last([2, 4, 4, 4, 6, 8], 5) is None
    assert first_and_last([2, 4, 6], 6) == (2, 2)
    assert first_and_last([7, 7, 7], 7) == (0, 2)
    assert first_and_last([7, 7, 7], 9) is None
    assert first_and_last([], 1) is None


@pytest.mark.id("tst_6vgh4a")
def test_bisect():
    """Matches bisect_left and bisect_right"""
    rng = random.Random(49)
    for _ in range(300):
        numbers = sorted(rng.randint(-4, 4) for _ in range(rng.randint(0, 12)))
        value = rng.randint(-5, 5)
        assert first_and_last(numbers, value) == by_bisect(numbers, value)


@pytest.mark.id("tst_w1it9k")
def test_long():
    """Searches long runs many times in time"""
    rng = random.Random(50)
    numbers = [position // RUN for position in range(NUMBERS)]
    values = [rng.randint(-1, NUMBERS // RUN) for _ in range(SEARCHES)]
    expected = [
        (value * RUN, value * RUN + RUN - 1) if 0 <= value < NUMBERS // RUN else None
        for value in values
    ]
    assert [first_and_last(numbers, value) for value in values] == expected
