import random

import pytest

from parts import parts

LETTERS = 200_000


def every_cut(text):
    """The sizes, by cutting at every place no letter falls on both sides of."""
    cuts = [
        place
        for place in range(1, len(text))
        if not set(text[:place]) & set(text[place:])
    ]
    ends = [*cuts, len(text)] if text else []
    return [end - start for start, end in zip([0, *cuts], ends)]


@pytest.mark.id("tst_o161wr")
def test_parts():
    """Cuts the text into the most parts, each letter in one"""
    assert parts("ababcbacadefegdehijhklij") == [9, 7, 8]


@pytest.mark.id("tst_k9az3t")
def test_edges():
    """Handles no letters, one, every letter different, and one part"""
    assert parts("") == []
    assert parts("a") == [1]
    assert parts("abc") == [1, 1, 1]
    assert parts("eccbbbbdec") == [10]


@pytest.mark.id("tst_j7vlmc")
def test_random():
    """Matches checking every place to cut, on random texts"""
    rng = random.Random(621)
    for _ in range(300):
        text = "".join(rng.choice("abcde") for _ in range(rng.randint(0, 14)))
        assert parts(text) == every_cut(text)


@pytest.mark.id("tst_9f9itq")
def test_long():
    """Cuts a long text in time"""
    blocks = "".join(letter * (LETTERS // 25) for letter in "abcdefghijklmnopqrstuvwxy")
    assert parts(blocks) == [LETTERS // 25] * 25
    assert parts("z" + blocks[1:-1] + "z") == [LETTERS]
