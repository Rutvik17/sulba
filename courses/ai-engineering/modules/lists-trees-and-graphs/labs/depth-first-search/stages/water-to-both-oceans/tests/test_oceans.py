import random

import pytest

from oceans import both_oceans

SIDE = 300
STEPS = ((1, 0), (-1, 0), (0, 1), (0, -1))
GRID = [
    [1, 2, 2, 3, 5],
    [3, 2, 3, 4, 4],
    [2, 4, 5, 3, 1],
    [6, 7, 1, 4, 5],
    [5, 1, 1, 2, 4],
]


def from_each_square(heights):
    """The answer, by following the rain downhill from every square."""
    rows, columns = len(heights), len(heights[0])
    found = []
    for row in range(rows):
        for column in range(columns):
            seen, waiting = {(row, column)}, [(row, column)]
            while waiting:
                r, c = waiting.pop()
                for down, across in STEPS:
                    square = (r + down, c + across)
                    if (
                        0 <= square[0] < rows
                        and 0 <= square[1] < columns
                        and square not in seen
                        and heights[square[0]][square[1]] <= heights[r][c]
                    ):
                        seen.add(square)
                        waiting.append(square)
            pacific = any(r == 0 or c == 0 for r, c in seen)
            atlantic = any(r == rows - 1 or c == columns - 1 for r, c in seen)
            if pacific and atlantic:
                found.append((row, column))
    return found


@pytest.mark.id("tst_76fhwe")
def test_both_oceans():
    """Gives the squares whose rain reaches both oceans"""
    assert both_oceans(GRID) == [(0, 4), (1, 3), (1, 4), (2, 2), (3, 0), (3, 1), (4, 0)]


@pytest.mark.id("tst_54nzda")
def test_edges():
    """Handles one square, one row and a flat grid"""
    assert both_oceans([[7]]) == [(0, 0)]
    assert both_oceans([[1, 2, 3]]) == [(0, 0), (0, 1), (0, 2)]
    assert both_oceans([[4, 4], [4, 4]]) == [(0, 0), (0, 1), (1, 0), (1, 1)]


@pytest.mark.id("tst_04l2f3")
def test_random():
    """Matches following the rain from every square, on random grids"""
    rng = random.Random(721)
    for _ in range(300):
        rows, columns = rng.randint(1, 5), rng.randint(1, 5)
        heights = [[rng.randint(0, 3) for _ in range(columns)] for _ in range(rows)]
        assert both_oceans(heights) == from_each_square(heights)


@pytest.mark.id("tst_r5eohw")
def test_long():
    """Finds the squares of a large grid in time"""
    rng = random.Random(722)
    # A mountain whose every square drains to every edge.
    mountain = [
        [min(r, c, SIDE - 1 - r, SIDE - 1 - c) for c in range(SIDE)]
        for r in range(SIDE)
    ]
    assert both_oceans(mountain) == [(r, c) for r in range(SIDE) for c in range(SIDE)]
    # A basin: only its flat rim drains, along the rim, to both oceans.
    basin = [
        [-min(r, c, SIDE - 1 - r, SIDE - 1 - c) for c in range(SIDE)]
        for r in range(SIDE)
    ]
    rim = [(r, c) for r in range(SIDE) for c in range(SIDE) if basin[r][c] == 0]
    assert both_oceans(basin) == rim
    heights = [[rng.randint(0, 10) for _ in range(SIDE)] for _ in range(SIDE)]
    found = both_oceans(heights)
    assert found == sorted(set(found))
