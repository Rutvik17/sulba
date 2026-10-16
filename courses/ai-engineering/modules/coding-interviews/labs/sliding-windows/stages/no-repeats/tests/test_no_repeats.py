import random

import pytest
from no_repeats import longest_unique

CHARACTERS = 100_000
KINDS = 20_000


def every_run(text):
    """The longest run with no repeats, by checking every run."""
    return max(
        (
            stop - start
            for start in range(len(text))
            for stop in range(start + 1, len(text) + 1)
            if len(set(text[start:stop])) == stop - start
        ),
        default=0,
    )


@pytest.mark.id("tst_00j1vu")
def test_unique():
    """Finds the longest run without a repeat"""
    assert longest_unique("tomato pot") == 6


@pytest.mark.id("tst_i0gdtk")
def test_edges():
    """Handles no text, one character repeated, and a text with no repeats"""
    assert longest_unique("") == 0
    assert longest_unique("aaaa") == 1
    assert longest_unique("abcd") == 4


@pytest.mark.id("tst_0igrjm")
def test_earlier():
    """Keeps a window that starts after a character's earlier copy"""
    assert longest_unique("abba") == 2
    assert longest_unique("dvdf") == 3


@pytest.mark.id("tst_i8b14c")
def test_every_run():
    """Matches checking every run"""
    rng = random.Random(36)
    for _ in range(300):
        text = "".join(rng.choices("abcd ", k=rng.randint(0, 12)))
        assert longest_unique(text) == every_run(text)


@pytest.mark.id("tst_vzfvva")
def test_long():
    """Finds a long run without a repeat in time"""
    text = "".join(chr(0x4E00 + i % KINDS) for i in range(CHARACTERS))
    assert longest_unique(text) == KINDS
