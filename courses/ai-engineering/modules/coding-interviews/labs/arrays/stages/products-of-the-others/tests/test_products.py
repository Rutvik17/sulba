import math
import random

import pytest
from products import products_of_others

NUMBERS = 100_000


def others(numbers):
    """Each position's product of the other numbers, multiplied afresh."""
    return [math.prod(numbers[:i] + numbers[i + 1 :]) for i in range(len(numbers))]


@pytest.mark.id("tst_tuust6")
def test_products():
    """Multiplies every number but each one"""
    assert products_of_others([2, 3, 4, 5]) == [60, 40, 30, 24]


@pytest.mark.id("tst_31sjpv")
def test_zeros():
    """Handles one zero, and two"""
    assert products_of_others([2, 0, 4]) == [0, 8, 0]
    assert products_of_others([0, 3, 0, 5]) == [0, 0, 0, 0]


@pytest.mark.id("tst_g04d6p")
def test_short():
    """Gives [1] for one number, and [] for none"""
    assert products_of_others([7]) == [1]
    assert products_of_others([]) == []


@pytest.mark.id("tst_q6psxg")
def test_others():
    """Matches the product of the other numbers"""
    rng = random.Random(7)
    for _ in range(300):
        numbers = [rng.randint(-5, 5) for _ in range(rng.randint(0, 10))]
        assert products_of_others(numbers) == others(numbers)


@pytest.mark.id("tst_5y5w1r")
def test_long():
    """Handles a long list in time"""
    rng = random.Random(8)
    numbers = [rng.choice([-1, 1]) for _ in range(NUMBERS)]
    zero = NUMBERS // 4
    numbers[zero] = 0
    rest = math.prod(numbers[:zero] + numbers[zero + 1 :])
    assert products_of_others(numbers) == [
        rest if i == zero else 0 for i in range(NUMBERS)
    ]
