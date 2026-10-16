import random

import pytest
from brackets import balanced

CHARACTERS = 200_000


def by_removing(text):
    """Whether the brackets balance, by removing touching pairs until none is left."""
    brackets = "".join(c for c in text if c in "()[]{}")
    while True:
        shorter = brackets.replace("()", "").replace("[]", "").replace("{}", "")
        if shorter == brackets:
            return brackets == ""
        brackets = shorter


@pytest.mark.id("tst_wlomr2")
def test_balanced():
    """Accepts brackets closed in order, and ignores other characters"""
    assert balanced("{[a](b)}") is True
    assert balanced("") is True
    assert balanced("no brackets") is True


@pytest.mark.id("tst_adn7do")
def test_unbalanced():
    """Rejects brackets crossed, left open, or closed with nothing open"""
    assert balanced("([)]") is False
    assert balanced("((") is False
    assert balanced("())") is False
    assert balanced("}") is False


@pytest.mark.id("tst_ijfrw9")
def test_removing():
    """Matches removing touching pairs"""
    rng = random.Random(42)
    for _ in range(300):
        text = "".join(rng.choices("()[]{}a", k=rng.randint(0, 12)))
        assert balanced(text) is by_removing(text)


@pytest.mark.id("tst_omei2f")
def test_long():
    """Checks deeply nested brackets in time"""
    depth = CHARACTERS // 2
    assert balanced("(" * depth + ")" * depth) is True
    assert balanced("(" * depth + ")" * (depth - 1) + "]") is False
