import random

import pytest

from pairs import smallest_pairs

SIZE = 100_000
K = 1_000


def every_pair(first, second, k):
    ranked = sorted(
        (a + b, i, j) for i, a in enumerate(first) for j, b in enumerate(second)
    )
    return [(first[i], second[j]) for _, i, j in ranked[:k]]


@pytest.mark.id("tst_hokfaf")
def test_smallest_pairs():
    """Gives the pairs with the smallest sums"""
    assert smallest_pairs([1, 7, 11], [2, 4, 6], 3) == [(1, 2), (1, 4), (1, 6)]


@pytest.mark.id("tst_vr8q2l")
def test_edges():
    """Handles an empty list, fewer pairs than k, and equal sums"""
    assert smallest_pairs([], [1, 2], 3) == []
    assert smallest_pairs([1, 2], [3], 5) == [(1, 3), (2, 3)]
    assert smallest_pairs([1, 1, 2], [1, 2, 3], 2) == [(1, 1), (1, 1)]
    assert smallest_pairs([1, 2], [1, 2], 3) == [(1, 1), (1, 2), (2, 1)]


@pytest.mark.id("tst_thw184")
def test_random():
    """Matches sorting every pair, on random lists"""
    rng = random.Random(251)
    for _ in range(300):
        first = sorted(rng.randint(-10, 10) for _ in range(rng.randint(0, 8)))
        second = sorted(rng.randint(-10, 10) for _ in range(rng.randint(0, 8)))
        k = rng.randint(1, 30)
        assert smallest_pairs(first, second, k) == every_pair(first, second, k)


@pytest.mark.id("tst_4wj9h7")
def test_long():
    """Gives the smallest pairs of long lists in time"""
    rng = random.Random(252)
    first = sorted(rng.randint(0, 10**9) for _ in range(SIZE))
    second = sorted(rng.randint(0, 10**9) for _ in range(SIZE))
    found = smallest_pairs(first, second, K)
    assert len(found) == K
    assert found == every_pair(first[:K], second[:K], K)
