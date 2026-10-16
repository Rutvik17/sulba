import random

import pytest
from lengths import decode, encode

CHARACTERS = 200_000


def runs_of(text):
    """Each run as (character, length), by walking the text."""
    runs = []
    for character in text:
        if runs and runs[-1][0] == character:
            runs[-1][1] += 1
        else:
            runs.append([character, 1])
    return "".join(f"{character}{length}" for character, length in runs)


@pytest.mark.id("tst_0s3q42")
def test_encode():
    """Writes each run as its character and length"""
    assert encode("aaabccdddd") == "a3b1c2d4"
    assert encode("x" * 12) == "x12"


@pytest.mark.id("tst_wlpxg0")
def test_decode():
    """Reads lengths of one digit or several"""
    assert decode("a3b1c2d4") == "aaabccdddd"
    assert decode("x12y1") == "x" * 12 + "y"


@pytest.mark.id("tst_2hx28d")
def test_empty():
    """Encodes and decodes an empty text, and one character"""
    assert encode("") == ""
    assert decode("") == ""
    assert encode("z") == "z1"
    assert decode("z1") == "z"


@pytest.mark.id("tst_yme57s")
def test_walking():
    """Matches walking the runs, and decodes what it encodes"""
    rng = random.Random(21)
    for _ in range(300):
        text = "".join(
            rng.choice("ab ") * rng.randint(1, 13) for _ in range(rng.randint(0, 5))
        )
        assert encode(text) == runs_of(text)
        assert decode(encode(text)) == text


@pytest.mark.id("tst_15pfrd")
def test_long():
    """Encodes and decodes a long text in time"""
    rng = random.Random(22)
    pieces, length = [], 0
    while length < CHARACTERS:
        run = rng.choice("abc") * min(rng.randint(1, 30), CHARACTERS - length)
        pieces.append(run)
        length += len(run)
    text = "".join(pieces)
    encoded = encode(text)
    assert encoded == runs_of(text)
    assert decode(encoded) == text
