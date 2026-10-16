import random

import pytest
from kth import kth_largest

NUMBERS = 200_000
K = 100_000


@pytest.mark.id("tst_3binlt")
def test_kth():
    """Finds the kth largest, counting repeats"""
    assert kth_largest([3, 9, 2, 9, 5], 2) == 9
    assert kth_largest([3, 9, 2, 9, 5], 3) == 5


@pytest.mark.id("tst_q61vlp")
def test_ends():
    """Gives the largest for k of 1 and the smallest for k of the list's length"""
    assert kth_largest([4, -1, 7], 1) == 7
    assert kth_largest([4, -1, 7], 3) == -1
    assert kth_largest([6], 1) == 6


@pytest.mark.id("tst_nmh87h")
def test_sorted():
    """Matches sorting the numbers"""
    rng = random.Random(60)
    for _ in range(300):
        numbers = [rng.randint(-9, 9) for _ in range(rng.randint(1, 12))]
        k = rng.randint(1, len(numbers))
        assert kth_largest(numbers, k) == sorted(numbers)[-k]


@pytest.mark.id("tst_o6ad2g")
def test_long():
    """Finds the kth largest of many numbers in time"""
    rng = random.Random(61)
    numbers = list(range(NUMBERS))
    rng.shuffle(numbers)
    assert kth_largest(numbers, K) == NUMBERS - K
