import random

import pytest

from regions import captured

SIDE = 300
STEPS = ((1, 0), (-1, 0), (0, 1), (0, -1))


def each_region(board):
    """The captured board, by searching each O's region and checking whether it touches the edge."""
    rows, columns = len(board), len(board[0]) if board else 0
    found = [list(row) for row in board]
    for row in range(rows):
        for column in range(columns):
            if board[row][column] != "O":
                continue
            region, waiting = {(row, column)}, [(row, column)]
            while waiting:
                r, c = waiting.pop()
                for down, across in STEPS:
                    square = (r + down, c + across)
                    if (
                        0 <= square[0] < rows
                        and 0 <= square[1] < columns
                        and board[square[0]][square[1]] == "O"
                        and square not in region
                    ):
                        region.add(square)
                        waiting.append(square)
            if not any(r in (0, rows - 1) or c in (0, columns - 1) for r, c in region):
                found[row][column] = "X"
    return ["".join(row) for row in found]


def winding(joined):
    """A board with one region that winds row by row, joined to the edge or not."""
    rows = [["X"] * SIDE for _ in range(SIDE)]
    for row in range(1, SIDE - 1, 2):
        for column in range(1, SIDE - 1):
            rows[row][column] = "O"
        if row + 1 < SIDE - 1:
            rows[row + 1][SIDE - 2 if row // 2 % 2 == 0 else 1] = "O"
    if joined:
        rows[1][0] = "O"
    return ["".join(row) for row in rows]


@pytest.mark.id("tst_ge85ft")
def test_captured():
    """Captures the regions that don't touch the edge"""
    assert captured(["XXXX", "XOOX", "XXOX", "XOXX"]) == [
        "XXXX",
        "XXXX",
        "XXXX",
        "XOXX",
    ]


@pytest.mark.id("tst_6wisb8")
def test_edges():
    """Handles no rows, one square, a board of Os, and a region in the middle"""
    assert captured([]) == []
    assert captured(["O"]) == ["O"]
    assert captured(["OOO", "OOO", "OOO"]) == ["OOO", "OOO", "OOO"]
    assert captured(["XXX", "XOX", "XXX"]) == ["XXX", "XXX", "XXX"]


@pytest.mark.id("tst_yi599t")
def test_random():
    """Matches searching each region, on random boards"""
    rng = random.Random(711)
    for _ in range(300):
        rows, columns = rng.randint(1, 6), rng.randint(1, 6)
        board = ["".join(rng.choice("XO") for _ in range(columns)) for _ in range(rows)]
        assert captured(board) == each_region(board)


@pytest.mark.id("tst_bbl8fu")
def test_long():
    """Keeps and captures a long winding region in time"""
    board = winding(joined=True)
    assert captured(board) == board
    assert captured(winding(joined=False)) == ["X" * SIDE] * SIDE
