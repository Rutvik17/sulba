from itertools import permutations

import pytest

from queens import queens

SIZE = 11


def every_order(size):
    """The placements, by trying every order of the columns, one queen to a row."""
    return sum(
        len({row + column for row, column in enumerate(order)}) == size
        and len({row - column for row, column in enumerate(order)}) == size
        for order in permutations(range(size))
    )


@pytest.mark.id("tst_19bcri")
def test_queens():
    """Counts the ways to place the queens"""
    assert queens(4) == 2
    assert queens(8) == 92


@pytest.mark.id("tst_hy2wlu")
def test_edges():
    """Counts one way for one queen, and none for 2 or 3"""
    assert queens(1) == 1
    assert queens(2) == 0
    assert queens(3) == 0


@pytest.mark.id("tst_1hgioo")
def test_every_order():
    """Matches trying every order of the columns, up to 7 queens"""
    for size in range(1, 8):
        assert queens(size) == every_order(size)


@pytest.mark.id("tst_v80orn")
def test_long():
    """Counts the ways for 10 and 11 queens in time"""
    assert queens(10) == 724
    assert queens(SIZE) == 2_680
