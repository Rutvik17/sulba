import random

import pytest
from fire import minutes_to_burn

SIDE = 401


def simulated(rows):
    """The minutes until every tree burns, by redrawing the whole map each minute."""
    squares = [list(row) for row in rows]
    minutes = 0
    while any("T" in row for row in squares):
        catching = [
            (y, x)
            for y, row in enumerate(squares)
            for x, square in enumerate(row)
            if square == "T"
            and any(
                0 <= ny < len(squares) and 0 <= nx < len(row) and squares[ny][nx] == "F"
                for ny, nx in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1))
            )
        ]
        if not catching:
            return -1
        for y, x in catching:
            squares[y][x] = "F"
        minutes += 1
    return minutes


def winding(side):
    """A square forest whose trees run along every other row, joined at alternate ends, with
    the fire in the top left corner."""
    rows = []
    for y in range(side):
        if y % 2 == 0:
            rows.append("T" * side)
        elif y % 4 == 1:
            rows.append("." * (side - 1) + "T")
        else:
            rows.append("T" + "." * (side - 1))
    rows[0] = "F" + rows[0][1:]
    return rows


@pytest.mark.id("tst_xo5vq7")
def test_minutes_to_burn():
    """Counts the minutes until the forest has burnt through"""
    assert minutes_to_burn(["F.TT", "TTT.", ".T.F"]) == 5


@pytest.mark.id("tst_6fclsj")
def test_edges():
    """Gives 0 with nothing left to burn, and -1 for a tree that can't catch"""
    assert minutes_to_burn([]) == 0
    assert minutes_to_burn(["..", ".."]) == 0
    assert minutes_to_burn(["F"]) == 0
    assert minutes_to_burn(["T"]) == -1
    assert minutes_to_burn(["F.T"]) == -1
    assert minutes_to_burn(["FTTF"]) == 1


@pytest.mark.id("tst_c6u34l")
def test_random():
    """Matches a minute by minute redrawing of the map, in random forests"""
    rng = random.Random(103)
    for _ in range(300):
        height, width = rng.randint(1, 8), rng.randint(1, 8)
        weights = [rng.random(), rng.random(), rng.random() * 0.3]
        rows = ["".join(rng.choices("T.F", weights, k=width)) for _ in range(height)]
        assert minutes_to_burn(rows) == simulated(rows)


@pytest.mark.id("tst_e2gook")
def test_long():
    """Follows a fire through a large forest in time"""
    trees = (SIDE + 1) // 2 * SIDE + SIDE // 2
    rows = winding(SIDE)
    assert minutes_to_burn(rows) == trees - 1
    cut_off = rows + ["." * SIDE, "T" + "." * (SIDE - 1)]
    assert minutes_to_burn(cut_off) == -1
