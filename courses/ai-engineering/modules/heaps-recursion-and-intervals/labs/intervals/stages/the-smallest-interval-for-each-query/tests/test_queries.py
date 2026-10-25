import random

import pytest

from queries import smallest_containing

INTERVALS = 100_000
QUERIES = 100_000


def every_interval(intervals, queries):
    """The answers, by checking every interval for every query."""
    return [
        min(
            (right - left + 1 for left, right in intervals if left <= query <= right),
            default=-1,
        )
        for query in queries
    ]


@pytest.mark.id("tst_2efhoe")
def test_smallest_containing():
    """Gives the size of the smallest interval holding each query"""
    assert smallest_containing([(1, 4), (2, 4), (3, 6), (4, 4)], [2, 3, 4, 5]) == [
        3,
        3,
        1,
        4,
    ]
    assert smallest_containing([(2, 3), (2, 5), (1, 8), (20, 25)], [2, 19, 5, 22]) == [
        2,
        -1,
        4,
        6,
    ]


@pytest.mark.id("tst_9zr7u7")
def test_edges():
    """Handles no intervals, no queries, a repeated query and an interval of one number"""
    assert smallest_containing([], [1, 2]) == [-1, -1]
    assert smallest_containing([(1, 3)], []) == []
    assert smallest_containing([(1, 3), (2, 2)], [2, 2, 3]) == [1, 1, 3]


@pytest.mark.id("tst_7cji0k")
def test_random():
    """Matches checking every interval for every query, on random lists"""
    rng = random.Random(551)
    for _ in range(300):
        intervals = [
            (left, left + rng.randint(0, 8))
            for left in (rng.randint(0, 30) for _ in range(rng.randint(0, 8)))
        ]
        queries = [rng.randint(0, 40) for _ in range(rng.randint(0, 8))]
        assert smallest_containing(intervals, queries) == every_interval(
            intervals, queries
        )


@pytest.mark.id("tst_g7tnwa")
def test_long():
    """Answers many queries over many intervals in time"""
    rng = random.Random(552)
    # Intervals nested around 0, each one wider than the last, and queries spread across them.
    intervals = [(-size, size) for size in range(INTERVALS)]
    rng.shuffle(intervals)
    queries = [rng.randint(-INTERVALS, INTERVALS) for _ in range(QUERIES)]
    expected = [
        2 * abs(query) + 1 if abs(query) < INTERVALS else -1 for query in queries
    ]
    assert smallest_containing(intervals, queries) == expected
