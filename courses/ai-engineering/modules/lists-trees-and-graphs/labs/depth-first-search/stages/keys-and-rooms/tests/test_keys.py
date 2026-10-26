import random
from collections import deque

import pytest

from keys import all_opened

ROOMS = 100_000


def level_by_level(rooms):
    """Whether every room opens, by a breadth-first search from room 0."""
    opened, waiting = {0}, deque([0])
    while waiting:
        for key in rooms[waiting.popleft()]:
            if key not in opened:
                opened.add(key)
                waiting.append(key)
    return len(opened) == len(rooms)


@pytest.mark.id("tst_l1dvyx")
def test_all_opened():
    """Tells whether every room can be entered"""
    assert all_opened([[1], [2], [3], []]) is True
    assert all_opened([[1, 3], [3, 0, 1], [2], [0]]) is False


@pytest.mark.id("tst_wk65yg")
def test_edges():
    """Handles one room, a room with no way in, and keys to rooms already open"""
    assert all_opened([[]]) is True
    assert all_opened([[], []]) is False
    assert all_opened([[0, 0, 1], [0, 1]]) is True


@pytest.mark.id("tst_dg6zlj")
def test_random():
    """Matches a breadth-first search, on random rooms"""
    rng = random.Random(701)
    for _ in range(300):
        count = rng.randint(1, 8)
        rooms = [
            [rng.randrange(count) for _ in range(rng.randint(0, 3))]
            for _ in range(count)
        ]
        assert all_opened(rooms) is level_by_level(rooms)


@pytest.mark.id("tst_awapd0")
def test_long():
    """Opens a long chain of rooms in time"""
    chain = [[room + 1] for room in range(ROOMS - 1)] + [[]]
    assert all_opened(chain) is True
    chain[ROOMS // 2] = []
    assert all_opened(chain) is False
    assert all_opened([list(range(1, ROOMS))] + [[] for _ in range(ROOMS - 1)]) is True
