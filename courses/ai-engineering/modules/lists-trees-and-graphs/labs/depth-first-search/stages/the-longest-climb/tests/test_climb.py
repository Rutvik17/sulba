import random

import pytest

from climb import longest_climb

SIDE = 300
STEPS = ((1, 0), (-1, 0), (0, 1), (0, -1))


def with_a_memo(heights):
    """The longest climb, by a search that calls itself, with a memo."""
    rows, columns = len(heights), len(heights[0])
    memo = {}

    def longest(r, c):
        if (r, c) not in memo:
            higher = [
                longest(r + down, c + across)
                for down, across in STEPS
                if 0 <= r + down < rows
                and 0 <= c + across < columns
                and heights[r + down][c + across] > heights[r][c]
            ]
            memo[r, c] = 1 + max(higher, default=0)
        return memo[r, c]

    return max(longest(r, c) for r in range(rows) for c in range(columns))


def snake(side):
    """A grid whose heights rise along a snake, row by row, turning at each end."""
    heights = [[0] * side for _ in range(side)]
    height = 0
    for row in range(side):
        for column in range(side) if row % 2 == 0 else range(side - 1, -1, -1):
            heights[row][column] = height
            height += 1
    return heights


@pytest.mark.id("tst_rp0u65")
def test_longest_climb():
    """Gives the length of the longest climb"""
    assert longest_climb([[9, 9, 4], [6, 6, 8], [2, 1, 1]]) == 4
    assert longest_climb([[3, 4, 5], [3, 2, 6], [2, 2, 1]]) == 4


@pytest.mark.id("tst_yq3st8")
def test_edges():
    """Handles one square, a flat grid and one row"""
    assert longest_climb([[5]]) == 1
    assert longest_climb([[2, 2], [2, 2]]) == 1
    assert longest_climb([[1, 2, 3, 2, 1]]) == 3


@pytest.mark.id("tst_1pchza")
def test_random():
    """Matches a search with a memo, on random grids"""
    rng = random.Random(741)
    for _ in range(300):
        rows, columns = rng.randint(1, 6), rng.randint(1, 6)
        heights = [[rng.randint(0, 9) for _ in range(columns)] for _ in range(rows)]
        assert longest_climb(heights) == with_a_memo(heights)


@pytest.mark.id("tst_4fm8c6")
def test_long():
    """Finds the longest climb of a large grid in time"""
    assert longest_climb(snake(SIDE)) == SIDE * SIDE
