import random

import pytest
from rain import trapped_water

BARS = 100_000


def by_scanning(heights):
    """The water, by finding the highest bar on each side of each bar."""
    return sum(
        max(0, min(max(heights[: i + 1]), max(heights[i:])) - height)
        for i, height in enumerate(heights)
    )


@pytest.mark.id("tst_4ywh0r")
def test_water():
    """Adds up the water above each bar"""
    assert trapped_water([3, 0, 2, 0, 4, 1, 2]) == 8


@pytest.mark.id("tst_r98g8a")
def test_spills():
    """Holds nothing when the water spills off, or there are fewer than three bars"""
    assert trapped_water([1, 2, 3, 4]) == 0
    assert trapped_water([4, 3, 2, 1]) == 0
    assert trapped_water([2, 0]) == 0
    assert trapped_water([]) == 0


@pytest.mark.id("tst_todjgt")
def test_scanning():
    """Matches scanning both sides of each bar"""
    rng = random.Random(32)
    for _ in range(300):
        heights = [rng.randint(0, 6) for _ in range(rng.randint(0, 14))]
        assert trapped_water(heights) == by_scanning(heights)


@pytest.mark.id("tst_d5ctkp")
def test_long():
    """Adds up the water in a long row in time"""
    rng = random.Random(33)
    heights = [rng.randint(0, 100) for _ in range(BARS)]
    # Walls at both ends, higher than every other bar, hold water up to their height.
    heights[0] = heights[-1] = 200
    assert trapped_water(heights) == sum(200 - height for height in heights[1:-1])
