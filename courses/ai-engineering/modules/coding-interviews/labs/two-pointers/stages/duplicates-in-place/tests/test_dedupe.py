import random

import pytest
from dedupe import dedupe

NUMBERS = 1_000_000


def assert_deduped(numbers):
    """dedupe leaves numbers' different values at its front, in order, and counts them."""
    values = sorted(set(numbers))
    same = numbers
    count = dedupe(numbers)
    assert numbers is same
    assert count == len(values)
    assert numbers[:count] == values


@pytest.mark.id("tst_u5a78e")
def test_dedupe():
    """Moves the different values to the front and counts them"""
    numbers = [1, 1, 2, 3, 3, 3, 7]
    assert dedupe(numbers) == 4
    assert numbers[:4] == [1, 2, 3, 7]


@pytest.mark.id("tst_cml5o7")
def test_edges():
    """Handles no numbers, one value repeated, and no repeats"""
    assert dedupe([]) == 0
    assert_deduped([5, 5, 5])
    assert_deduped([-2, 0, 4, 9])


@pytest.mark.id("tst_tbzq11")
def test_set():
    """Matches the sorted set of the numbers"""
    rng = random.Random(27)
    for _ in range(300):
        assert_deduped(sorted(rng.randint(-5, 5) for _ in range(rng.randint(0, 14))))


@pytest.mark.id("tst_93ibdg")
def test_long():
    """Dedupes a long list in time"""
    numbers = [value for value in range(NUMBERS // 2) for _ in range(2)]
    assert dedupe(numbers) == NUMBERS // 2
    assert numbers[: NUMBERS // 2] == list(range(NUMBERS // 2))
