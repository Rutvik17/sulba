import random

import pytest
from spiral import spiral


def walk(grid):
    """The spiral by walking: step on until the next cell is off the grid or read, then turn right."""
    rows, columns = len(grid), len(grid[0]) if grid else 0
    read = set()
    order = []
    row, column, down, across = 0, 0, 0, 1
    for _ in range(rows * columns):
        order.append(grid[row][column])
        read.add((row, column))
        ahead = (row + down, column + across)
        if not (0 <= ahead[0] < rows and 0 <= ahead[1] < columns) or ahead in read:
            down, across = across, -down
        row, column = row + down, column + across
    return order


@pytest.mark.id("tst_s7nk0d")
def test_spiral():
    """Reads a grid in a spiral"""
    grid = [["a", "b", "c"], ["d", "e", "f"], ["g", "h", "i"], ["j", "k", "l"]]
    assert spiral(grid) == ["a", "b", "c", "f", "i", "l", "k", "j", "g", "d", "e", "h"]


@pytest.mark.id("tst_0bjjz5")
def test_thin():
    """Reads a grid of one row, one column or one value, and an empty grid"""
    assert spiral([[1, 2, 3]]) == [1, 2, 3]
    assert spiral([[1], [2], [3]]) == [1, 2, 3]
    assert spiral([[5]]) == [5]
    assert spiral([]) == []


@pytest.mark.id("tst_d6z10i")
def test_wide_and_tall():
    """Reads grids wider than they are tall, and taller than they are wide"""
    assert spiral([[1, 2, 3, 4, 5], [6, 7, 8, 9, 10]]) == [
        1,
        2,
        3,
        4,
        5,
        10,
        9,
        8,
        7,
        6,
    ]
    tall = [[1, 2], [3, 4], [5, 6], [7, 8], [9, 10]]
    assert spiral(tall) == [1, 2, 4, 6, 8, 10, 9, 7, 5, 3]


@pytest.mark.id("tst_ulppg5")
def test_walk():
    """Matches walking the grid and turning right at each edge"""
    rng = random.Random(9)
    for _ in range(200):
        rows, columns = rng.randint(1, 8), rng.randint(1, 8)
        grid = [[rng.randint(0, 99) for _ in range(columns)] for _ in range(rows)]
        assert spiral(grid) == walk(grid)
