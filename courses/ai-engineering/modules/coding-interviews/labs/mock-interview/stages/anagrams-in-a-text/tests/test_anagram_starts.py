import random
from collections import Counter

import pytest
from anagram_starts import anagram_starts

CHARACTERS = 100_000
LENGTH = 4_000


def by_sorting(text, word):
    """The anagrams' starts, by sorting each run of the word's length."""
    length, target = len(word), sorted(word)
    return [
        start
        for start in range(len(text) - length + 1)
        if sorted(text[start : start + length]) == target
    ]


def by_counting(text, word):
    """The anagrams' starts, by comparing each window's counts with the word's."""
    length, target = len(word), dict(Counter(word))
    window = dict(Counter(text[:length]))
    starts = [0] if len(text) >= length and window == target else []
    for start in range(1, len(text) - length + 1):
        leaving, coming = text[start - 1], text[start + length - 1]
        if window[leaving] == 1:
            del window[leaving]
        else:
            window[leaving] -= 1
        window[coming] = window.get(coming, 0) + 1
        if window == target:
            starts.append(start)
    return starts


@pytest.mark.id("tst_13cjvg")
def test_anagrams():
    """Finds where each anagram starts"""
    assert anagram_starts("listen silent enlist", "inlets") == [0, 7, 14]


@pytest.mark.id("tst_ja5nd6")
def test_overlap():
    """Finds anagrams that overlap, and counts repeated characters"""
    assert anagram_starts("abab", "ab") == [0, 1, 2]
    assert anagram_starts("aaa", "aa") == [0, 1]
    assert anagram_starts("aab", "ab") == [1]


@pytest.mark.id("tst_zkm25b")
def test_none():
    """Gives [] when no run is an anagram, or the word is longer than the text"""
    assert anagram_starts("abc", "d") == []
    assert anagram_starts("ab", "abc") == []
    assert anagram_starts("", "a") == []


@pytest.mark.id("tst_8aaa2t")
def test_sorting():
    """Matches sorting each run"""
    rng = random.Random(68)
    for _ in range(300):
        text = "".join(rng.choices("ab c", k=rng.randint(0, 14)))
        word = "".join(rng.choices("abc", k=rng.randint(1, 3)))
        assert anagram_starts(text, word) == by_sorting(text, word)


@pytest.mark.id("tst_amo1vn")
def test_long():
    """Finds the anagrams of a long word in a long text in time"""
    rng = random.Random(69)
    letters = "abcdefghijklmnopqrstuvwxyz"
    word = "".join(rng.choices(letters, k=LENGTH))
    pieces = []
    while sum(map(len, pieces)) < CHARACTERS - LENGTH:
        if rng.random() < 0.1:
            pieces.append("".join(rng.sample(word, LENGTH)))
        else:
            pieces.append("".join(rng.choices(letters, k=rng.randint(1, 50))))
    text = "".join(pieces)[: CHARACTERS - LENGTH] + "".join(rng.sample(word, LENGTH))
    assert len(text) == CHARACTERS
    assert anagram_starts(text, word) == by_counting(text, word)
