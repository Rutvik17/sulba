import random
from collections import Counter

import pytest
from cover import smallest_cover

CHARACTERS = 100_000
X = 30_000
Y = 70_000


def every_run(text, letters):
    """The first of the shortest runs covering letters, or "", by checking every run."""
    needed = Counter(letters)
    best = ""
    for start in range(len(text)):
        for stop in range(start + 1, len(text) + 1):
            run = text[start:stop]
            if (not best or len(run) < len(best)) and not needed - Counter(run):
                best = run
    return best


@pytest.mark.id("tst_wz8ngj")
def test_cover():
    """Finds the shortest run that covers the letters"""
    assert smallest_cover("banana bread", "brad") == "bread"
    assert smallest_cover("figure eight", "ight") == "ight"


@pytest.mark.id("tst_nwt38v")
def test_repeats():
    """Covers a letter as many times as it appears"""
    assert smallest_cover("abcabc", "aa") == "abca"
    assert smallest_cover("aab", "aab") == "aab"


@pytest.mark.id("tst_9ujc86")
def test_none():
    """Gives "" when no run covers the letters, and the first of runs that tie"""
    assert smallest_cover("abc", "d") == ""
    assert smallest_cover("", "a") == ""
    assert smallest_cover("ab ba", "ab") == "ab"


@pytest.mark.id("tst_3bqx4j")
def test_every_run():
    """Matches checking every run"""
    rng = random.Random(40)
    for _ in range(200):
        text = "".join(rng.choices("abc ", k=rng.randint(0, 12)))
        letters = "".join(rng.choices("abc", k=rng.randint(1, 3)))
        assert smallest_cover(text, letters) == every_run(text, letters)


@pytest.mark.id("tst_b23j50")
def test_long():
    """Finds the cover in a long text in time"""
    rng = random.Random(41)
    text = rng.choices("ab", k=CHARACTERS)
    text[X], text[Y] = "x", "y"
    text = "".join(text)
    assert smallest_cover(text, "xy") == text[X : Y + 1]
