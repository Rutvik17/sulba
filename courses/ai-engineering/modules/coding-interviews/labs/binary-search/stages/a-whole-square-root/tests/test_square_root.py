import math
import random

import pytest
from square_root import square_root

ROOT = 10**30 + 7
LARGEST = ROOT * ROOT - 1


@pytest.mark.id("tst_4jc6hf")
def test_root():
    """Finds the whole square root"""
    assert square_root(17) == 4
    assert square_root(16) == 4


@pytest.mark.id("tst_52ohhj")
def test_small():
    """Handles 0, 1 and the numbers either side of a square"""
    assert square_root(0) == 0
    assert square_root(1) == 1
    assert square_root(2) == 1
    assert square_root(99) == 9
    assert square_root(100) == 10


@pytest.mark.id("tst_5t68ur")
def test_isqrt():
    """Matches math.isqrt"""
    rng = random.Random(53)
    for _ in range(300):
        n = rng.randrange(10 ** rng.randint(1, 20))
        assert square_root(n) == math.isqrt(n)


@pytest.mark.id("tst_92ghsw")
def test_large():
    """Stays exact for numbers too large for a float"""
    assert square_root(LARGEST) == ROOT - 1
    assert square_root(LARGEST + 1) == ROOT
