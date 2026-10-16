import os.path
import random

import pytest
from prefixes import common_prefix


@pytest.mark.id("tst_tzw8tq")
def test_prefix():
    """Finds the prefix every word shares"""
    assert common_prefix(["interval", "internet", "interior"]) == "inter"


@pytest.mark.id("tst_sm0cxo")
def test_none():
    """Gives "" when the words share no prefix, there are none, or one is empty"""
    assert common_prefix(["cat", "dog"]) == ""
    assert common_prefix([]) == ""
    assert common_prefix(["abc", ""]) == ""


@pytest.mark.id("tst_ivmxti")
def test_whole():
    """Gives a whole word when it starts every word"""
    assert common_prefix(["solo"]) == "solo"
    assert common_prefix(["in", "inside", "into"]) == "in"
    assert common_prefix(["same", "same"]) == "same"


@pytest.mark.id("tst_fm6hg5")
def test_library():
    """Matches os.path.commonprefix"""
    rng = random.Random(20)
    for _ in range(300):
        stem = "".join(rng.choices("ab", k=rng.randint(0, 4)))
        words = [
            stem + "".join(rng.choices("ab", k=rng.randint(0, 3)))
            for _ in range(rng.randint(0, 6))
        ]
        assert common_prefix(words) == os.path.commonprefix(words)
