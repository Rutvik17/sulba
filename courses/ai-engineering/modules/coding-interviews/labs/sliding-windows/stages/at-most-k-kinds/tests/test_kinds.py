import random

import pytest
from kinds import longest_with_kinds

ITEMS = 100_000
STRETCH = 80_000
K = 5


def every_run(items, k):
    """The longest run with at most k values, by checking every run."""
    return max(
        (
            stop - start
            for start in range(len(items))
            for stop in range(start + 1, len(items) + 1)
            if len(set(items[start:stop])) <= k
        ),
        default=0,
    )


@pytest.mark.id("tst_w93yfv")
def test_kinds():
    """Finds the longest run with at most k values"""
    assert longest_with_kinds(["a", "b", "a", "c", "c", "a", "b"], 2) == 4


@pytest.mark.id("tst_bezmlf")
def test_edges():
    """Handles k of 0, a k at least the number of values, and no items"""
    assert longest_with_kinds(["a", "b"], 0) == 0
    assert longest_with_kinds(["a", "b", "a"], 3) == 3
    assert longest_with_kinds([], 2) == 0


@pytest.mark.id("tst_72c8qv")
def test_every_run():
    """Matches checking every run"""
    rng = random.Random(39)
    for _ in range(300):
        items = rng.choices("abcd", k=rng.randint(0, 12))
        k = rng.randint(0, 4)
        assert longest_with_kinds(items, k) == every_run(items, k)


@pytest.mark.id("tst_m6j7j7")
def test_long():
    """Finds a long run in time"""
    items = [i % K for i in range(STRETCH)] + [K + i for i in range(ITEMS - STRETCH)]
    assert longest_with_kinds(items, K) == STRETCH
