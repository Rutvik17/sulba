import random

import pytest
from unique import first_unique

CHARACTERS = 300_000


def by_counting(text):
    """The first unique character's position, counting each character afresh."""
    for position, character in enumerate(text):
        if text.count(character) == 1:
            return position
    return None


@pytest.mark.id("tst_ospkpl")
def test_unique():
    """Finds the first character that appears once"""
    assert first_unique("referee") == 2


@pytest.mark.id("tst_maxkwf")
def test_none():
    """Gives None when every character repeats, or there are none"""
    assert first_unique("aabbcc") is None
    assert first_unique("") is None


@pytest.mark.id("tst_jh20o0")
def test_characters():
    """Counts case, spaces and punctuation as characters"""
    assert first_unique("x") == 0
    assert first_unique("Aa") == 0
    assert first_unique("a a!") == 1


@pytest.mark.id("tst_6sqjhh")
def test_counting():
    """Matches counting each character afresh"""
    rng = random.Random(12)
    for _ in range(300):
        text = "".join(rng.choice("abcd ") for _ in range(rng.randint(0, 12)))
        assert first_unique(text) == by_counting(text)


@pytest.mark.id("tst_ozcjkh")
def test_long():
    """Finds the first unique character in a long text in time"""
    text = "ab" * ((CHARACTERS - 2) // 2) + "c" + "a"
    assert len(text) == CHARACTERS
    assert first_unique(text) == CHARACTERS - 2
