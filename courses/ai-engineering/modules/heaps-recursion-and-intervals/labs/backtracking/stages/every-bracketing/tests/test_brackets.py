from itertools import product
from math import comb

import pytest

from brackets import bracketings

PAIRS = 12


def balanced(text):
    """Whether the brackets balance, by taking out each () until none is left."""
    while "()" in text:
        text = text.replace("()", "")
    return text == ""


@pytest.mark.id("tst_r6lx69")
def test_bracketings():
    """Gives every balanced string, in sorted order"""
    assert bracketings(3) == ["((()))", "(()())", "(())()", "()(())", "()()()"]


@pytest.mark.id("tst_5anmc5")
def test_edges():
    """Gives the empty string for no pairs, and one string for one pair"""
    assert bracketings(0) == [""]
    assert bracketings(1) == ["()"]
    assert bracketings(2) == ["(())", "()()"]


@pytest.mark.id("tst_pajww5")
def test_every_string():
    """Matches keeping the balanced strings of every string of brackets, up to 8 pairs"""
    for pairs in range(9):
        every = ["".join(text) for text in product("()", repeat=2 * pairs)]
        assert bracketings(pairs) == [text for text in every if balanced(text)]


@pytest.mark.id("tst_m0y540")
def test_long():
    """Gives every bracketing of 12 pairs in time"""
    found = bracketings(PAIRS)
    assert len(found) == comb(2 * PAIRS, PAIRS) // (PAIRS + 1)
    assert found == sorted(set(found))
    assert all(len(text) == 2 * PAIRS and balanced(text) for text in found)
