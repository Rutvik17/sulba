import random

import pytest
from sorted_pair import sorted_pair

NUMBERS = 200_000


def any_pair(numbers, target):
    """Whether any two numbers add up to target, by trying every pair."""
    return any(
        numbers[i] + numbers[j] == target for j in range(len(numbers)) for i in range(j)
    )


def assert_pair(numbers, target, found):
    """found is a pair that adds up to target."""
    i, j = found
    assert 0 <= i < j < len(numbers)
    assert numbers[i] + numbers[j] == target


@pytest.mark.id("tst_g625gu")
def test_pair():
    """Finds the pair that adds up"""
    assert sorted_pair([1, 3, 4, 6, 9, 11], 13) == (2, 4)


@pytest.mark.id("tst_tfocat")
def test_none():
    """Gives None when no two numbers add up, and never pairs a number with itself"""
    assert sorted_pair([1, 2, 4], 9) is None
    assert sorted_pair([2, 5], 4) is None
    assert sorted_pair([], 0) is None
    assert sorted_pair([2, 2, 5], 4) == (0, 1)


@pytest.mark.id("tst_kv9w69")
def test_any_pair():
    """Finds a pair whenever trying every pair finds one"""
    rng = random.Random(25)
    for _ in range(300):
        numbers = sorted(rng.randint(-10, 10) for _ in range(rng.randint(0, 12)))
        target = rng.randint(-15, 15)
        found = sorted_pair(numbers, target)
        if any_pair(numbers, target):
            assert_pair(numbers, target, found)
        else:
            assert found is None


@pytest.mark.id("tst_rbq63m")
def test_long():
    """Finds a pair in a long list in time"""
    rng = random.Random(26)
    numbers = sorted(rng.sample(range(0, 10**9, 2), NUMBERS))
    target = numbers[NUMBERS // 5] + numbers[NUMBERS // 2]
    assert_pair(numbers, target, sorted_pair(numbers, target))
    assert sorted_pair(numbers, 1) is None
