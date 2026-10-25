import random

import pytest
from islands import islands

SIDE = 401


def brute(rows):
    """The islands on the map, by joining each land square to its neighbours in sets."""
    owner = {}
    for y, row in enumerate(rows):
        for x, square in enumerate(row):
            if square == "#":
                owner[y, x] = {(y, x)}
    for y, x in list(owner):
        for near in ((y + 1, x), (y, x + 1)):
            if near in owner and owner[near] is not owner[y, x]:
                merged = owner[y, x] | owner[near]
                for square in merged:
                    owner[square] = merged
    return len({id(group) for group in owner.values()})


def snake(side):
    """A square map whose one island runs along every other row and joins them at alternate
    ends."""
    rows = []
    for y in range(side):
        if y % 2 == 0:
            rows.append("#" * side)
        elif y % 4 == 1:
            rows.append("." * (side - 1) + "#")
        else:
            rows.append("#" + "." * (side - 1))
    return rows


@pytest.mark.id("tst_gr2mmh")
def test_islands():
    """Counts the islands on a map"""
    assert islands(["##..#", "#...#", "..#..", ".....", "##.##"]) == 5


@pytest.mark.id("tst_3y6ed8")
def test_edges():
    """Counts none on an empty map or open water, and doesn't join squares at their corners"""
    assert islands([]) == 0
    assert islands(["...", "..."]) == 0
    assert islands(["#"]) == 1
    assert islands(["#.#", ".#.", "#.#"]) == 5
    assert islands(["###", "#.#", "###"]) == 1


@pytest.mark.id("tst_yk2psl")
def test_random():
    """Matches a count by joining neighbours, on random maps"""
    rng = random.Random(101)
    for _ in range(300):
        height, width = rng.randint(1, 12), rng.randint(1, 12)
        land = rng.random()
        rows = [
            "".join("#" if rng.random() < land else "." for _ in range(width))
            for _ in range(height)
        ]
        assert islands(rows) == brute(rows)


@pytest.mark.id("tst_0qjj73")
def test_long():
    """Counts a long winding island in time"""
    assert islands(snake(SIDE)) == 1
