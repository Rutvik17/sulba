import random

import pytest
from maze import shortest_way

SIDE = 401
ROOM = 300


def relaxed(rows):
    """The steps to the exit, by lowering each square's steps from its neighbours' until
    nothing changes."""
    far = len(rows) * len(rows[0]) + 1
    steps = {
        (y, x): 0 if square == "S" else far
        for y, row in enumerate(rows)
        for x, square in enumerate(row)
        if square != "#"
    }
    changed = True
    while changed:
        changed = False
        for (y, x), now in steps.items():
            for near in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)):
                if near in steps and steps[near] + 1 < now:
                    now = steps[y, x] = steps[near] + 1
                    changed = True
    (end,) = [square for square in steps if rows[square[0]][square[1]] == "E"]
    return -1 if steps[end] == far else steps[end]


def corridors(side):
    """A square maze of corridors along every other row, joined at alternate ends, from the
    start in the top left corner to the exit at the end of the last corridor."""
    rows = []
    for y in range(side):
        if y % 2 == 0:
            rows.append("." * side)
        elif y % 4 == 1:
            rows.append("#" * (side - 1) + ".")
        else:
            rows.append("." + "#" * (side - 1))
    rows[0] = "S" + rows[0][1:]
    last = rows[-1]
    rows[-1] = last[:-1] + "E" if (side - 1) % 4 == 0 else "E" + last[1:]
    return rows


@pytest.mark.id("tst_q43xfu")
def test_shortest_way():
    """Counts the steps of the shortest way out"""
    assert shortest_way(["S.#.....", ".##.###.", "....#E..", ".##....."]) == 9


@pytest.mark.id("tst_sjpyrl")
def test_edges():
    """Gives 1 for an exit next to the start, and -1 when walls shut it off"""
    assert shortest_way(["SE"]) == 1
    assert shortest_way(["S", ".", "E"]) == 2
    assert shortest_way(["S#E"]) == -1
    assert shortest_way(["S.#", "###", "..E"]) == -1


@pytest.mark.id("tst_9ha3mn")
def test_random():
    """Matches the steps found by lowering each square's from its neighbours', in random
    mazes"""
    rng = random.Random(102)
    for _ in range(300):
        height, width = rng.randint(1, 9), rng.randint(2, 9)
        walls = rng.random() * 0.5
        squares = [
            ["#" if rng.random() < walls else "." for _ in range(width)]
            for _ in range(height)
        ]
        start, end = rng.sample(
            [(y, x) for y in range(height) for x in range(width)], 2
        )
        squares[start[0]][start[1]] = "S"
        squares[end[0]][end[1]] = "E"
        rows = ["".join(row) for row in squares]
        assert shortest_way(rows) == relaxed(rows)


@pytest.mark.id("tst_maewxb")
def test_long():
    """Finds the way out of a long maze and across a wide open room in time"""
    corridors_ = (SIDE + 1) // 2
    assert shortest_way(corridors(SIDE)) == corridors_ * SIDE + SIDE // 2 - 1
    room = ["." * ROOM for _ in range(ROOM)]
    room[0] = "S" + room[0][1:]
    room[-1] = room[-1][:-1] + "E"
    assert shortest_way(room) == 2 * (ROOM - 1)
