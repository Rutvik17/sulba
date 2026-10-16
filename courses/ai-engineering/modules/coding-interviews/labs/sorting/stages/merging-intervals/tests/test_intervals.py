import random

import pytest
from intervals import merge_intervals

INTERVALS = 100_000


def by_pairs(intervals):
    """The merged intervals, by merging any two that overlap until no two do."""
    found = list(intervals)
    merging = True
    while merging:
        merging = False
        for i in range(len(found)):
            for j in range(i + 1, len(found)):
                (a, b), (c, d) = found[i], found[j]
                if a <= d and c <= b:
                    found[i] = (min(a, c), max(b, d))
                    del found[j]
                    merging = True
                    break
            if merging:
                break
    return sorted(found)


@pytest.mark.id("tst_ozvxx6")
def test_merge():
    """Merges the intervals that overlap, sorted by start"""
    intervals = [(4, 7), (1, 3), (9, 12), (2, 5), (12, 14)]
    assert merge_intervals(intervals) == [(1, 7), (9, 14)]


@pytest.mark.id("tst_ji031r")
def test_edges():
    """Merges intervals inside others and ones that touch, and handles none"""
    assert merge_intervals([(1, 10), (2, 3)]) == [(1, 10)]
    assert merge_intervals([(3, 5), (1, 3)]) == [(1, 5)]
    assert merge_intervals([(5, 5), (1, 2)]) == [(1, 2), (5, 5)]
    assert merge_intervals([]) == []


@pytest.mark.id("tst_fapeaf")
def test_pairs():
    """Matches merging any two that overlap until no two do"""
    rng = random.Random(56)
    for _ in range(300):
        intervals = []
        for _ in range(rng.randint(0, 8)):
            start = rng.randint(0, 20)
            intervals.append((start, start + rng.randint(0, 5)))
        assert merge_intervals(intervals) == by_pairs(intervals)


@pytest.mark.id("tst_y217v7")
def test_long():
    """Merges many intervals in time"""
    rng = random.Random(57)
    # Each block of ten holds two intervals that overlap, and no block touches another.
    intervals = [(10 * i, 10 * i + 4) for i in range(INTERVALS // 2)]
    intervals += [(10 * i + 2, 10 * i + 6) for i in range(INTERVALS // 2)]
    rng.shuffle(intervals)
    assert merge_intervals(intervals) == [
        (10 * i, 10 * i + 6) for i in range(INTERVALS // 2)
    ]
