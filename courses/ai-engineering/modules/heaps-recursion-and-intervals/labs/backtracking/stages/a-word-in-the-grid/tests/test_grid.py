import random

import pytest

from grid import traced

SIDE = 40
PREFIX = 30
STEPS = ((1, 0), (-1, 0), (0, 1), (0, -1))


def every_path(grid, word):
    """Whether any path spells the word, by trying every path from every cell."""
    rows, columns = len(grid), len(grid[0])

    def follow(path):
        if len(path) == len(word):
            return True
        row, column = path[-1]
        for down, across in STEPS:
            r, c = row + down, column + across
            if 0 <= r < rows and 0 <= c < columns and (r, c) not in path:
                if grid[r][c] == word[len(path)] and follow(path + [(r, c)]):
                    return True
        return False

    return any(
        grid[row][column] == word[0] and follow([(row, column)])
        for row in range(rows)
        for column in range(columns)
    )


def planted(rng, side, length):
    """A grid of random letters with a random word written along a random path in it."""
    cells = [[rng.choice("ABCD") for _ in range(side)] for _ in range(side)]
    while True:
        path = [(rng.randrange(side), rng.randrange(side))]
        while len(path) < length:
            row, column = path[-1]
            steps = [
                (row + down, column + across)
                for down, across in STEPS
                if 0 <= row + down < side
                and 0 <= column + across < side
                and (row + down, column + across) not in path
            ]
            if not steps:
                break
            path.append(rng.choice(steps))
        if len(path) == length:
            break
    word = "".join(rng.choice("ABCD") for _ in range(length))
    for (row, column), letter in zip(path, word):
        cells[row][column] = letter
    return ["".join(row) for row in cells], word


@pytest.mark.id("tst_9ufcn5")
def test_traced():
    """Tells whether a word can be traced through the grid"""
    grid = ["ABCE", "SFCS", "ADEE"]
    assert traced(grid, "ABCCED") is True
    assert traced(grid, "SEE") is True
    assert traced(grid, "ABCB") is False


@pytest.mark.id("tst_kqjalg")
def test_edges():
    """Handles one cell, a word longer than the grid, and a cell used twice"""
    assert traced(["A"], "A") is True
    assert traced(["A"], "B") is False
    assert traced(["AA"], "AAA") is False
    assert traced(["AB"], "ABA") is False
    assert traced(["AB", "BA"], "ABAB") is True


@pytest.mark.id("tst_45mukp")
def test_random():
    """Matches trying every path, on random grids"""
    rng = random.Random(411)
    for _ in range(300):
        rows, columns = rng.randint(1, 4), rng.randint(1, 4)
        grid = ["".join(rng.choice("AB") for _ in range(columns)) for _ in range(rows)]
        word = "".join(rng.choice("AB") for _ in range(rng.randint(1, 6)))
        assert traced(grid, word) is every_path(grid, word)


@pytest.mark.id("tst_s5v8om")
def test_long():
    """Traces words through a 40 by 40 grid in time"""
    rng = random.Random(412)
    grid, word = planted(rng, SIDE, SIDE)
    assert traced(grid, word) is True
    assert traced(["A" * SIDE] * SIDE, "A" * PREFIX + "B") is False
