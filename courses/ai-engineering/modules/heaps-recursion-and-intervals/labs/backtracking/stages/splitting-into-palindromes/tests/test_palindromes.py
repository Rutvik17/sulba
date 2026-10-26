import random
from itertools import product

import pytest

from palindromes import splits

REPEATED = 18
LETTERS = 40


def every_cut(text):
    """The splits, by trying every set of cuts between letters."""
    found = []
    for cuts in product([False, True], repeat=max(len(text) - 1, 0)):
        parts, start = [], 0
        for place, cut in enumerate(cuts, start=1):
            if cut:
                parts.append(text[start:place])
                start = place
        if text:
            parts.append(text[start:])
        if all(part == part[::-1] for part in parts):
            found.append(parts)
    return found


@pytest.mark.id("tst_1zoxph")
def test_splits():
    """Gives every split into palindromes"""
    assert sorted(splits("aab")) == [["a", "a", "b"], ["aa", "b"]]


@pytest.mark.id("tst_36fvo7")
def test_edges():
    """Handles no letters, one, and a text that is a palindrome"""
    assert splits("") == [[]]
    assert splits("a") == [["a"]]
    assert splits("ab") == [["a", "b"]]
    assert sorted(splits("aba")) == [["a", "b", "a"], ["aba"]]


@pytest.mark.id("tst_wrytwc")
def test_random():
    """Matches trying every set of cuts, on random texts"""
    rng = random.Random(421)
    for _ in range(200):
        text = "".join(rng.choice("ab") for _ in range(rng.randint(0, 10)))
        assert sorted(splits(text)) == sorted(every_cut(text))


@pytest.mark.id("tst_d7iuwc")
def test_long():
    """Splits long texts in time"""
    found = splits("a" * REPEATED)
    assert len(found) == 2 ** (REPEATED - 1)
    assert len({tuple(parts) for parts in found}) == len(found)
    assert all("".join(parts) == "a" * REPEATED for parts in found)
    text = "abcdefghij" * (LETTERS // 10)
    assert splits(text) == [list(text)]
