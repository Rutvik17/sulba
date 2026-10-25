import random

import pytest

from insert import inserted

INTERVALS = 200_000


def merged(intervals):
    """The intervals merged, by sorting them and joining each to the last when they overlap."""
    found = []
    for start, end in sorted(intervals):
        if found and start <= found[-1][1]:
            found[-1] = (found[-1][0], max(found[-1][1], end))
        else:
            found.append((start, end))
    return found


@pytest.mark.id("tst_nqx4al")
def test_inserted():
    """Inserts an interval and merges those it overlaps"""
    assert inserted([(1, 3), (6, 9)], (2, 5)) == [(1, 5), (6, 9)]
    assert inserted([(1, 2), (3, 5), (6, 7), (8, 10), (12, 16)], (4, 8)) == [
        (1, 2),
        (3, 10),
        (12, 16),
    ]


@pytest.mark.id("tst_zue9tn")
def test_edges():
    """Handles no intervals, an interval before or after all of them, one that touches, and one that covers all"""
    assert inserted([], (4, 8)) == [(4, 8)]
    assert inserted([(5, 7)], (1, 2)) == [(1, 2), (5, 7)]
    assert inserted([(5, 7)], (9, 9)) == [(5, 7), (9, 9)]
    assert inserted([(1, 3), (6, 9)], (3, 6)) == [(1, 9)]
    assert inserted([(2, 3), (5, 6)], (0, 10)) == [(0, 10)]


@pytest.mark.id("tst_9uel1g")
def test_random():
    """Matches merging the whole list again, on random intervals"""
    rng = random.Random(501)
    for _ in range(300):
        intervals = merged(
            [
                (start, start + rng.randint(0, 5))
                for start in (rng.randint(0, 40) for _ in range(rng.randint(0, 7)))
            ]
        )
        start = rng.randint(0, 45)
        new = (start, start + rng.randint(0, 8))
        assert inserted(intervals, new) == merged(intervals + [new])


@pytest.mark.id("tst_pl5n86")
def test_long():
    """Inserts into a long list in time"""
    rng = random.Random(502)
    ends = sorted(rng.sample(range(10**9), 2 * INTERVALS))
    intervals = [(ends[2 * n], ends[2 * n + 1]) for n in range(INTERVALS)]
    found, added = intervals, []
    for _ in range(5):
        start = rng.randrange(10**9)
        added.append((start, start + 10**6))
        found = inserted(found, added[-1])
    assert found == merged(intervals + added)
