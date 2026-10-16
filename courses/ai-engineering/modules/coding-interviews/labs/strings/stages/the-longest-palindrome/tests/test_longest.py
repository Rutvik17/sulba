import random

import pytest
from longest import longest_palindrome


def every_run(text):
    """The longest palindrome, the first of those that tie, by checking every run."""
    best = ""
    for start in range(len(text)):
        for stop in range(start + 1, len(text) + 1):
            run = text[start:stop]
            if len(run) > len(best) and run == run[::-1]:
                best = run
    return best


@pytest.mark.id("tst_tefo0c")
def test_odd():
    """Finds a palindrome of odd length"""
    assert longest_palindrome("abacabad") == "abacaba"


@pytest.mark.id("tst_ixaon9")
def test_even():
    """Finds a palindrome of even length"""
    assert longest_palindrome("xabbay") == "abba"
    assert longest_palindrome("cc") == "cc"


@pytest.mark.id("tst_kkwrvh")
def test_ties():
    """Gives the first of palindromes that tie, and "" for no text"""
    assert longest_palindrome("abcd") == "a"
    assert longest_palindrome("aabb") == "aa"
    assert longest_palindrome("") == ""


@pytest.mark.id("tst_n7zk21")
def test_every_run():
    """Matches checking every run"""
    rng = random.Random(24)
    for _ in range(300):
        text = "".join(rng.choices("ab ", k=rng.randint(0, 14)))
        assert longest_palindrome(text) == every_run(text)
