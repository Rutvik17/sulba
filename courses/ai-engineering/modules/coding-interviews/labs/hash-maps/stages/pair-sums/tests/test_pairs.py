import random

import pytest
from pairs import pair_sum

NUMBERS = 100_000


def every_pair(numbers, target):
    """The pair that ends first, and of those the one that starts first, by trying them all."""
    for j in range(len(numbers)):
        for i in range(j):
            if numbers[i] + numbers[j] == target:
                return (i, j)
    return None


@pytest.mark.id("tst_tqj4l9")
def test_pair():
    """Finds the pair that ends first"""
    assert pair_sum([5, 2, 9, 6, 3], 8) == (1, 3)


@pytest.mark.id("tst_jw6fox")
def test_no_pair():
    """Gives None when no two numbers add up, and never pairs a number with itself"""
    assert pair_sum([1, 2, 4], 9) is None
    assert pair_sum([4, 1], 8) is None
    assert pair_sum([], 0) is None


@pytest.mark.id("tst_8sgyun")
def test_equal():
    """Pairs two equal numbers"""
    assert pair_sum([3, 3], 6) == (0, 1)
    assert pair_sum([1, 3, 2, 3], 6) == (1, 3)


@pytest.mark.id("tst_ww2p0y")
def test_every_pair():
    """Matches trying every pair"""
    rng = random.Random(10)
    for _ in range(300):
        numbers = [rng.randint(-10, 10) for _ in range(rng.randint(0, 12))]
        target = rng.randint(-15, 15)
        assert pair_sum(numbers, target) == every_pair(numbers, target)


@pytest.mark.id("tst_wv8o41")
def test_long():
    """Finds the pair in a long list in time"""
    rng = random.Random(11)
    # Different even numbers, then one odd number: the only pair that adds up to an odd target.
    numbers = rng.sample(range(0, 10**9, 2), NUMBERS - 1) + [1]
    partner = rng.randrange(NUMBERS - 1)
    assert pair_sum(numbers, numbers[partner] + 1) == (partner, NUMBERS - 1)
