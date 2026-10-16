import random

import pytest
from patterns import same_pattern

CHARACTERS = 200_000


def by_first_places(first, second):
    """Whether the texts follow the same pattern, by where each character first appears."""
    return [first.index(c) for c in first] == [second.index(c) for c in second]


@pytest.mark.id("tst_nawdgy")
def test_pattern():
    """Renames one text's characters into the other's"""
    assert same_pattern("paper", "title") is True


@pytest.mark.id("tst_vk2sun")
def test_one_to_one():
    """Allows no character renamed two ways, and no two renamed to the same one"""
    assert same_pattern("ab", "aa") is False
    assert same_pattern("aa", "ab") is False
    assert same_pattern("abca", "zyxw") is False


@pytest.mark.id("tst_wblfgd")
def test_lengths():
    """Gives False for different lengths, and True for two empty texts"""
    assert same_pattern("abc", "ab") is False
    assert same_pattern("", "") is True


@pytest.mark.id("tst_y0pce2")
def test_first_places():
    """Matches comparing where each character first appears"""
    rng = random.Random(23)
    for _ in range(300):
        length = rng.randint(0, 8)
        first = "".join(rng.choices("abc", k=length))
        second = "".join(rng.choices("xyz", k=length))
        assert same_pattern(first, second) is by_first_places(first, second)


@pytest.mark.id("tst_qgjmqw")
def test_long():
    """Compares long texts of different characters in time"""
    first = "".join(chr(0x20000 + i) for i in range(CHARACTERS))
    second = "".join(chr(0x60000 + i) for i in range(CHARACTERS))
    assert same_pattern(first, second) is True
    assert same_pattern(first, second[:-1] + second[0]) is False
