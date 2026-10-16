import random

import pytest
from palindromes import is_palindrome

CHARACTERS = 200_000


def by_filtering(text):
    """Whether the text is a palindrome, by keeping its letters and digits and reversing them."""
    kept = [character.lower() for character in text if character.isalnum()]
    return kept == kept[::-1]


@pytest.mark.id("tst_7inj8k")
def test_palindromes():
    """Reads letters and digits both ways"""
    assert is_palindrome("Step on no pets!") is True
    assert is_palindrome("Hello, world") is False


@pytest.mark.id("tst_ur3ha3")
def test_edges():
    """Ignores case and other characters, and counts digits"""
    assert is_palindrome("Aa") is True
    assert is_palindrome("1, 2 ... 2; 1") is True
    assert is_palindrome("ab1") is False
    assert is_palindrome("") is True
    assert is_palindrome("?! ,") is True


@pytest.mark.id("tst_fbfez6")
def test_filtering():
    """Matches keeping the letters and digits and reversing them"""
    rng = random.Random(18)
    for _ in range(300):
        half = "".join(rng.choices("aAbB1 ,", k=rng.randint(0, 6)))
        text = half + rng.choice(["", "a", "!"]) + half[::-1]
        if rng.random() < 0.5:
            text = "".join(rng.choices("aAbB1 ,", k=rng.randint(0, 12)))
        assert is_palindrome(text) is by_filtering(text)


@pytest.mark.id("tst_nhszkx")
def test_long():
    """Checks a long text in time"""
    rng = random.Random(19)
    half = "".join(rng.choices("abcde ,.", k=CHARACTERS // 2))
    text = half + half[::-1].upper()
    assert len(text) == CHARACTERS
    assert is_palindrome(text) is True
    assert is_palindrome(text[:-1] + "z") is False
