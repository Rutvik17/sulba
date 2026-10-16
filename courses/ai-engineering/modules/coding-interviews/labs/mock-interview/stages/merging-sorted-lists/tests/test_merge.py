import random
from itertools import chain

import pytest
from merge import merge_sorted

LISTS = 4_000
LENGTH = 50


@pytest.mark.id("tst_xmn4uc")
def test_merge():
    """Merges sorted lists into one"""
    assert merge_sorted([[1, 4, 9], [2, 3, 10], [5]]) == [1, 2, 3, 4, 5, 9, 10]


@pytest.mark.id("tst_k01w8u")
def test_edges():
    """Handles empty lists, no lists and equal numbers"""
    assert merge_sorted([[], [3], []]) == [3]
    assert merge_sorted([]) == []
    assert merge_sorted([[2, 2], [2]]) == [2, 2, 2]


@pytest.mark.id("tst_klio0f")
def test_sorted():
    """Matches sorting every number"""
    rng = random.Random(66)
    for _ in range(300):
        lists = [
            sorted(rng.randint(-9, 9) for _ in range(rng.randint(0, 5)))
            for _ in range(rng.randint(0, 5))
        ]
        assert merge_sorted(lists) == sorted(chain.from_iterable(lists))


@pytest.mark.id("tst_d8dqu6")
def test_long():
    """Merges many lists in time"""
    rng = random.Random(67)
    lists = [sorted(rng.randrange(10**6) for _ in range(LENGTH)) for _ in range(LISTS)]
    assert merge_sorted(lists) == sorted(chain.from_iterable(lists))
