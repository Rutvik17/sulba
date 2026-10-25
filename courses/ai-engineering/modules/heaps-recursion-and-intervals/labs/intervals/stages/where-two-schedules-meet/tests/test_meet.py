import random

import pytest

from meet import common

INTERVALS = 100_000


def disjoint(rng, count, span):
    """count sorted intervals that don't overlap, within 0 to span."""
    ends = sorted(rng.sample(range(span), 2 * count))
    return [(ends[2 * n], ends[2 * n + 1]) for n in range(count)]


def every_pair(first, second):
    """The common intervals, by comparing every pair."""
    found = []
    for a in first:
        for b in second:
            start, end = max(a[0], b[0]), min(a[1], b[1])
            if start <= end:
                found.append((start, end))
    return sorted(found)


@pytest.mark.id("tst_2sgwph")
def test_common():
    """Gives the intervals both lists cover"""
    first = [(0, 2), (5, 10), (13, 23), (24, 25)]
    second = [(1, 5), (8, 12), (15, 24), (25, 26)]
    assert common(first, second) == [
        (1, 2),
        (5, 5),
        (8, 10),
        (15, 23),
        (24, 24),
        (25, 25),
    ]


@pytest.mark.id("tst_pe2yjx")
def test_edges():
    """Handles an empty list, no overlap, and one interval inside another"""
    assert common([], [(1, 5)]) == []
    assert common([(1, 5)], []) == []
    assert common([(1, 2)], [(3, 4)]) == []
    assert common([(1, 10)], [(2, 3), (5, 7)]) == [(2, 3), (5, 7)]


@pytest.mark.id("tst_wx9du5")
def test_random():
    """Matches comparing every pair, on random lists"""
    rng = random.Random(511)
    for _ in range(300):
        first = disjoint(rng, rng.randint(0, 5), 30)
        second = disjoint(rng, rng.randint(0, 5), 30)
        assert common(first, second) == every_pair(first, second)


@pytest.mark.id("tst_dvvit8")
def test_long():
    """Finds the common intervals of long lists in time"""
    rng = random.Random(512)
    first = disjoint(rng, INTERVALS, 10**9)
    second = disjoint(rng, INTERVALS, 10**9)
    found = common(first, second)
    assert found == sorted(found)
    assert common(first, first) == first
    assert common(first, [(0, 10**9)]) == first
