import random

import pytest
from climb import furthest

BUILDINGS = 100_000


def reachable(heights, bricks, ladders, building):
    """Whether the building can be reached: the ladders take the highest steps up to it, and the
    bricks the rest."""
    steps = sorted(
        (later - earlier for earlier, later in zip(heights, heights[1 : building + 1])),
        reverse=True,
    )
    return sum(step for step in steps[ladders:] if step > 0) <= bricks


def one_by_one(heights, bricks, ladders):
    """The furthest building, checking each in turn by sorting the steps up to it."""
    reached = 0
    while reached + 1 < len(heights):
        if not reachable(heights, bricks, ladders, reached + 1):
            break
        reached += 1
    return reached


def by_halving(heights, bricks, ladders):
    """The furthest building, found by halving the range, since a building can be reached only
    if every one before it can."""
    low, high = 0, len(heights) - 1
    while low < high:
        middle = (low + high + 1) // 2
        if reachable(heights, bricks, ladders, middle):
            low = middle
        else:
            high = middle - 1
    return low


@pytest.mark.id("tst_mhlfy9")
def test_furthest():
    """Gives the furthest building reached"""
    assert furthest([3, 5, 4, 10, 12, 11, 17], 10, 1) == 6
    assert furthest([3, 5, 4, 10, 12, 11, 17], 4, 1) == 5


@pytest.mark.id("tst_lhv6no")
def test_edges():
    """Handles one building, no climbing, nothing to climb with, and bricks for every step"""
    assert furthest([7], 0, 0) == 0
    assert furthest([9, 8, 8, 2], 0, 0) == 3
    assert furthest([1, 2], 0, 0) == 0
    assert furthest([1, 4, 2, 6], 7, 0) == 3
    assert furthest([1, 4, 2, 6], 6, 0) == 2
    assert furthest([1, 4, 2, 6], 0, 2) == 3


@pytest.mark.id("tst_shbeok")
def test_random():
    """Matches checking each building in turn, on random rows"""
    rng = random.Random(801)
    for _ in range(300):
        heights = [rng.randint(0, 20) for _ in range(rng.randint(1, 25))]
        bricks, ladders = rng.randint(0, 40), rng.randint(0, 4)
        expected = one_by_one(heights, bricks, ladders)
        assert furthest(heights, bricks, ladders) == expected


@pytest.mark.id("tst_x5bkp5")
def test_long():
    """Gives the furthest building of a long row in time"""
    assert furthest(list(range(BUILDINGS)), 50_000, 1_000) == 51_000
    rng = random.Random(802)
    heights = [rng.randint(0, 1_000_000) for _ in range(BUILDINGS)]
    bricks, ladders = 2_000_000_000, 5_000
    assert furthest(heights, bricks, ladders) == by_halving(heights, bricks, ladders)
