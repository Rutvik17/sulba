import random

import pytest

from symbols import symbol

ROWS = 60


def written(rows):
    """Each row from 1 to rows, written out."""
    found = ["0"]
    while len(found) < rows:
        found.append("".join("01" if each == "0" else "10" for each in found[-1]))
    return found


@pytest.mark.id("tst_h2cx0p")
def test_symbol():
    """Gives a row's symbol at a place"""
    assert symbol(4, 5) == 1
    assert [symbol(4, place) for place in range(1, 9)] == [0, 1, 1, 0, 1, 0, 0, 1]


@pytest.mark.id("tst_jejrh5")
def test_edges():
    """Gives row 1's symbol, and the first and last places of a row"""
    assert symbol(1, 1) == 0
    assert symbol(2, 1) == 0
    assert symbol(2, 2) == 1
    assert symbol(5, 1) == 0
    assert symbol(5, 16) == 0


@pytest.mark.id("tst_o6uwcn")
def test_rows():
    """Matches every place of rows written out, up to row 12"""
    for row, text in enumerate(written(12), start=1):
        assert [symbol(row, place) for place in range(1, len(text) + 1)] == [
            int(each) for each in text
        ]


@pytest.mark.id("tst_hedf6q")
def test_long():
    """Gives symbols deep in row 60 in time"""
    rng = random.Random(301)
    assert symbol(ROWS, 1) == 0
    assert symbol(ROWS, 2 ** (ROWS - 1)) == 1
    for _ in range(2_000):
        place = rng.randint(1, 2 ** (ROWS - 1))
        assert symbol(ROWS, place) == bin(place - 1).count("1") % 2
