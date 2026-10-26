import random
from collections import deque

import pytest

from circle import survivor

PEOPLE = 1_000_000


def counted_out(people, step):
    """The last person left, by counting the circle out."""
    circle = deque(range(1, people + 1))
    while len(circle) > 1:
        circle.rotate(-(step - 1))
        circle.popleft()
    return circle[0]


@pytest.mark.id("tst_84yerc")
def test_survivor():
    """Gives the last person left in the circle"""
    assert survivor(5, 2) == 3
    assert survivor(6, 5) == 1


@pytest.mark.id("tst_yvv3qu")
def test_edges():
    """Handles one person, a step of 1, and a step longer than the circle"""
    assert survivor(1, 3) == 1
    assert survivor(4, 1) == 4
    assert survivor(3, 7) == counted_out(3, 7)


@pytest.mark.id("tst_vs8cbu")
def test_random():
    """Matches counting the circle out, for random circles and steps"""
    rng = random.Random(321)
    for _ in range(500):
        people, step = rng.randint(1, 60), rng.randint(1, 70)
        assert survivor(people, step) == counted_out(people, step)


@pytest.mark.id("tst_emi64i")
def test_long():
    """Finds the last one standing in a circle of 1,000,000 in time"""
    # With a step of 2, the survivor of 2 ** m + rest people is 2 * rest + 1.
    rest = PEOPLE - 2 ** (PEOPLE.bit_length() - 1)
    assert survivor(PEOPLE, 2) == 2 * rest + 1
    assert survivor(PEOPLE, 1) == PEOPLE
    assert survivor(100_000, 7) == counted_out(100_000, 7)
