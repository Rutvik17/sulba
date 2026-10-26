import itertools
import random
from collections import Counter

import pytest

from reorganize import reorganized

LETTERS = 200_000


def apart(text, found):
    return sorted(found) == sorted(text) and all(
        a != b for a, b in zip(found, found[1:])
    )


def possible(text):
    """Whether any order of the text keeps alike letters apart, by trying them all."""
    return any(
        apart(text, "".join(order)) for order in set(itertools.permutations(text))
    )


@pytest.mark.id("tst_m2zgve")
def test_reorganized():
    """Keeps alike letters apart, or gives "" when it can't"""
    assert reorganized("aab") == "aba"
    assert reorganized("aaab") == ""


@pytest.mark.id("tst_lbahi3")
def test_edges():
    """Handles no letters, one, and the most of one letter that still fits"""
    assert reorganized("") == ""
    assert reorganized("z") == "z"
    assert reorganized("zz") == ""
    assert apart("aaabb", reorganized("aaabb"))
    assert reorganized("aaaabb") == ""


@pytest.mark.id("tst_rkl3d3")
def test_random():
    """Matches trying every order, on random texts"""
    rng = random.Random(241)
    for _ in range(200):
        text = "".join(rng.choice("abc") for _ in range(rng.randint(1, 7)))
        found = reorganized(text)
        assert apart(text, found) if possible(text) else found == ""


@pytest.mark.id("tst_ctfixw")
def test_long():
    """Orders a long text in time"""
    rng = random.Random(242)
    letters = list("abcdefghij" * (LETTERS // 10))
    rng.shuffle(letters)
    text = "".join(letters)
    assert apart(text, reorganized(text))
    assert reorganized("a" * (LETTERS // 2 + 1) + "b" * (LETTERS // 2 - 1)) == ""
    assert Counter(reorganized("ab" * (LETTERS // 2))) == Counter("ab" * (LETTERS // 2))
