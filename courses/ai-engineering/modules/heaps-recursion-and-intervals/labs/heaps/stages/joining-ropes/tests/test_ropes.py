import random
from functools import cache

import pytest

from ropes import join_cost

ROPES = 200_000


def every_order(lengths):
    """The least cost, by trying every pair to join first, then every pair after it."""

    @cache
    def least(ropes):
        if len(ropes) < 2:
            return 0
        best = None
        for i in range(len(ropes)):
            for j in range(i + 1, len(ropes)):
                joined = ropes[i] + ropes[j]
                rest = ropes[:i] + ropes[i + 1 : j] + ropes[j + 1 :] + (joined,)
                cost = joined + least(tuple(sorted(rest)))
                best = cost if best is None else min(best, cost)
        return best

    return least(tuple(sorted(lengths)))


@pytest.mark.id("tst_mff1kx")
def test_join_cost():
    """Joins the ropes at the least cost"""
    assert join_cost([4, 3, 2, 6]) == 29


@pytest.mark.id("tst_ogqkhn")
def test_edges():
    """Costs nothing for no ropes or one, and the two lengths for two"""
    assert join_cost([]) == 0
    assert join_cost([7]) == 0
    assert join_cost([7, 5]) == 12
    assert join_cost([1, 1, 1, 1]) == 8


@pytest.mark.id("tst_z53byv")
def test_random():
    """Matches trying every order of joins, on random ropes"""
    rng = random.Random(201)
    for _ in range(150):
        lengths = [rng.randint(1, 30) for _ in range(rng.randint(0, 6))]
        assert join_cost(lengths) == every_order(lengths)


@pytest.mark.id("tst_yoxmz6")
def test_long():
    """Joins many ropes in time"""
    rng = random.Random(202)
    lengths = [rng.randint(1, 1_000_000) for _ in range(ROPES)]
    assert join_cost(lengths) > 0
    assert join_cost([1] * ROPES) == 3_537_856
