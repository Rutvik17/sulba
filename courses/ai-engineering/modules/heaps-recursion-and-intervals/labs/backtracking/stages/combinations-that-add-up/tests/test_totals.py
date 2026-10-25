import random
from itertools import combinations

import pytest

from totals import totals

NUMBERS = 40
ONES = 40


def every_subset(numbers, target):
    """The combinations, by trying every subset of the places."""
    found = set()
    for size in range(1, len(numbers) + 1):
        for chosen in combinations(sorted(numbers), size):
            if sum(chosen) == target:
                found.add(chosen)
    return sorted(found)


def distinct_ways(total, largest):
    """How many ways total is a sum of distinct numbers from 1 to largest."""
    ways = [1] + [0] * total
    for number in range(1, largest + 1):
        for amount in range(total, number - 1, -1):
            ways[amount] += ways[amount - number]
    return ways[total]


@pytest.mark.id("tst_1wovij")
def test_totals():
    """Gives every combination that adds up to the target, once each"""
    assert totals([10, 1, 2, 7, 6, 1, 5], 8) == [(1, 1, 6), (1, 2, 5), (1, 7), (2, 6)]


@pytest.mark.id("tst_eflvlk")
def test_edges():
    """Handles no numbers, no combination, and equal numbers"""
    assert totals([], 5) == []
    assert totals([2, 4], 5) == []
    assert totals([5], 5) == [(5,)]
    assert totals([3, 3, 3], 6) == [(3, 3)]


@pytest.mark.id("tst_tbu3k2")
def test_random():
    """Matches trying every subset, on random lists"""
    rng = random.Random(401)
    for _ in range(200):
        numbers = [rng.randint(1, 8) for _ in range(rng.randint(0, 11))]
        target = rng.randint(1, 20)
        assert totals(numbers, target) == every_subset(numbers, target)


@pytest.mark.id("tst_7frg8b")
def test_long():
    """Finds the combinations of long lists in time"""
    found = totals(list(range(NUMBERS, 0, -1)), 20)
    assert len(found) == distinct_ways(20, NUMBERS)
    assert found == sorted(set(found))
    assert all(sum(each) == 20 and list(each) == sorted(set(each)) for each in found)
    assert totals([1] * ONES, ONES // 2) == [(1,) * (ONES // 2)]
    assert totals([1] * 25 + [50], 26) == []
