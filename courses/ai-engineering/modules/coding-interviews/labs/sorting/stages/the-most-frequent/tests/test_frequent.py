import random
from collections import Counter

import pytest
from frequent import most_frequent

ITEMS = 200_000
KINDS = 20_000


def by_counter(items, k):
    """The k most frequent items, from Counter.most_common."""
    return [item for item, _ in Counter(items).most_common(k)]


@pytest.mark.id("tst_73qefb")
def test_frequent():
    """Gives the most frequent items, most frequent first"""
    items = ["b", "a", "c", "a", "b", "a", "d"]
    assert most_frequent(items, 2) == ["a", "b"]


@pytest.mark.id("tst_ew1tw8")
def test_ties():
    """Keeps items that tie in the order they first appear"""
    items = ["b", "a", "c", "a", "b", "a", "d"]
    assert most_frequent(items, 3) == ["a", "b", "c"]
    assert most_frequent(["z", "y", "x"], 3) == ["z", "y", "x"]


@pytest.mark.id("tst_cqt8qm")
def test_counter():
    """Matches Counter.most_common"""
    rng = random.Random(64)
    for _ in range(300):
        items = rng.choices("abcde", k=rng.randint(1, 14))
        k = rng.randint(1, len(set(items)))
        assert most_frequent(items, k) == by_counter(items, k)


@pytest.mark.id("tst_84tdcj")
def test_long():
    """Finds the most frequent of many items in time"""
    rng = random.Random(65)
    items = [rng.randrange(KINDS) for _ in range(ITEMS)]
    assert most_frequent(items, 100) == by_counter(items, 100)
