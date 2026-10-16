import random

import pytest
from water import most_water

LINES = 100_000


def every_pair(heights):
    """The most water, by measuring every pair of lines."""
    return max(
        (
            min(heights[i], heights[j]) * (j - i)
            for j in range(len(heights))
            for i in range(j)
        ),
        default=0,
    )


@pytest.mark.id("tst_dbo83u")
def test_water():
    """Finds the most water two lines hold"""
    assert most_water([2, 7, 3, 6, 4, 8, 1]) == 28


@pytest.mark.id("tst_39v7th")
def test_edges():
    """Gives 0 for fewer than two lines, and handles equal heights"""
    assert most_water([]) == 0
    assert most_water([5]) == 0
    assert most_water([4, 4]) == 4
    assert most_water([3, 3, 3, 3]) == 9


@pytest.mark.id("tst_i4gkdm")
def test_every_pair():
    """Matches measuring every pair"""
    rng = random.Random(28)
    for _ in range(300):
        heights = [rng.randint(0, 9) for _ in range(rng.randint(0, 12))]
        assert most_water(heights) == every_pair(heights)


@pytest.mark.id("tst_4x0kse")
def test_long():
    """Finds the most water in a long row in time"""
    rng = random.Random(29)
    heights = [rng.randint(1, 1000) for _ in range(LINES)]
    # The two end lines are the tallest, so they hold the most: 5,000 times the widest gap.
    heights[0] = heights[-1] = 5000
    assert most_water(heights) == 5000 * (LINES - 1)
