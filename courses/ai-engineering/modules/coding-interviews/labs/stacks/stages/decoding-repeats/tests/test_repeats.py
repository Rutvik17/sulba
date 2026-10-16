import random
import re

import pytest
from repeats import decode

INNERMOST = re.compile(r"(\d+)\[([a-z]*)\]")


def by_replacing(text):
    """The decoded text, by writing out innermost repeats until none is left."""
    while "[" in text:
        text = INNERMOST.sub(lambda match: match[2] * int(match[1]), text)
    return text


def encoded(rng, depth):
    """A random encoded text."""
    parts = []
    for _ in range(rng.randint(1, 3)):
        if depth and rng.random() < 0.5:
            parts.append(f"{rng.randint(1, 3)}[{encoded(rng, depth - 1)}]")
        else:
            parts.append("".join(rng.choices("abc", k=rng.randint(0, 2))))
    return "".join(parts)


@pytest.mark.id("tst_sbgxm1")
def test_decode():
    """Writes out each repeat"""
    assert decode("3[ab]2[c]") == "abababcc"


@pytest.mark.id("tst_ou9zws")
def test_nested():
    """Writes out repeats inside repeats"""
    assert decode("x2[y3[z]]") == "xyzzzyzzz"
    assert decode("2[a2[b2[c]]]") == "abccbccabccbcc"


@pytest.mark.id("tst_dbwa33")
def test_counts():
    """Reads counts of several digits, and text with no repeats"""
    assert decode("10[a]") == "a" * 10
    assert decode("12[xy]z") == "xy" * 12 + "z"
    assert decode("plain") == "plain"
    assert decode("") == ""


@pytest.mark.id("tst_qb4umh")
def test_replacing():
    """Matches writing out innermost repeats first"""
    rng = random.Random(46)
    for _ in range(300):
        text = encoded(rng, 3)
        assert decode(text) == by_replacing(text)
