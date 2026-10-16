import random

import pytest
from rotated import rotated_search

NUMBERS = 200_000
SEARCHES = 50_000


def by_index(numbers, value):
    """The position of value, by reading the list from its start."""
    return numbers.index(value) if value in numbers else None


@pytest.mark.id("tst_tz0355")
def test_rotated():
    """Finds a value in a rotated list"""
    assert rotated_search([15, 18, 22, 3, 7, 11], 7) == 4
    assert rotated_search([15, 18, 22, 3, 7, 11], 18) == 1


@pytest.mark.id("tst_b8srlx")
def test_edges():
    """Handles a missing value, no rotation, one number and no numbers"""
    assert rotated_search([15, 18, 22, 3, 7, 11], 5) is None
    assert rotated_search([3, 7, 11, 15], 11) == 2
    assert rotated_search([4], 4) == 0
    assert rotated_search([], 4) is None


@pytest.mark.id("tst_xkui5e")
def test_index():
    """Matches reading the list from its start, for every rotation"""
    rng = random.Random(51)
    for _ in range(150):
        ordered = sorted(rng.sample(range(-20, 20), rng.randint(1, 9)))
        for turn in range(len(ordered)):
            numbers = ordered[turn:] + ordered[:turn]
            value = rng.randint(-21, 21)
            assert rotated_search(numbers, value) == by_index(numbers, value)


@pytest.mark.id("tst_0abqk3")
def test_long():
    """Searches a long rotated list many times in time"""
    rng = random.Random(52)
    turn = 70_000
    ordered = list(range(0, 3 * NUMBERS, 3))
    numbers = ordered[turn:] + ordered[:turn]
    values = [rng.randrange(3 * NUMBERS) for _ in range(SEARCHES)]
    # Number 3k sits at position k - turn, wrapped round, and no other number is there.
    expected = [
        (value // 3 - turn) % NUMBERS if value % 3 == 0 else None for value in values
    ]
    assert [rotated_search(numbers, value) for value in values] == expected
