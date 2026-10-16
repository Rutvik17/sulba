import random

import pytest
from ranges import range_sums

NUMBERS = 100_000
RANGES = 100_000


def ranges_of(rng, length, count):
    """count ranges of a list of this length, each with start <= stop."""
    return [
        tuple(sorted((rng.randrange(length + 1), rng.randrange(length + 1))))
        for _ in range(count)
    ]


@pytest.mark.id("tst_la5z7d")
def test_ranges():
    """Sums each range"""
    assert range_sums([3, -1, 4, 1, 5], [(0, 2), (1, 4), (2, 2)]) == [2, 4, 0]


@pytest.mark.id("tst_ym03yd")
def test_ends():
    """Sums ranges at either end, the whole list and empty ranges"""
    numbers = [3, -1, 4, 1, 5]
    assert range_sums(numbers, [(0, 5), (0, 1), (4, 5), (0, 0), (5, 5)]) == [
        12,
        3,
        5,
        0,
        0,
    ]
    assert range_sums([], [(0, 0)]) == [0]
    assert range_sums(numbers, []) == []


@pytest.mark.id("tst_d70im2")
def test_slices():
    """Matches the sum of each slice"""
    rng = random.Random(1)
    for _ in range(200):
        numbers = [rng.randint(-50, 50) for _ in range(rng.randint(0, 15))]
        ranges = ranges_of(rng, len(numbers), 10)
        assert range_sums(numbers, ranges) == [
            sum(numbers[start:stop]) for start, stop in ranges
        ]


@pytest.mark.id("tst_we5aqy")
def test_long():
    """Sums many ranges of a long list in time"""
    rng = random.Random(2)
    numbers = [rng.randint(-1000, 1000) for _ in range(NUMBERS)]
    ranges = ranges_of(rng, NUMBERS, RANGES)
    sums = range_sums(numbers, ranges)
    assert len(sums) == RANGES
    for at in rng.sample(range(RANGES), 20):
        start, stop = ranges[at]
        assert sums[at] == sum(numbers[start:stop])
