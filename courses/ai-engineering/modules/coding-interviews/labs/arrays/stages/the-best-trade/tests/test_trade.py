import random

import pytest
from trade import best_profit

PRICES = 100_000


def every_trade(prices):
    """The best of every trade, or 0."""
    days = range(len(prices))
    return max(
        [0]
        + [prices[sell] - prices[buy] for buy in days for sell in days if sell > buy]
    )


@pytest.mark.id("tst_j3i2hy")
def test_trade():
    """Finds the best trade"""
    assert best_profit([9, 4, 6, 2, 8, 5]) == 6


@pytest.mark.id("tst_bocrtn")
def test_no_trade():
    """Gives 0 when no trade makes money"""
    assert best_profit([8, 6, 6, 3, 1]) == 0
    assert best_profit([5]) == 0
    assert best_profit([]) == 0


@pytest.mark.id("tst_j3fjpd")
def test_every_trade():
    """Matches the best of every trade"""
    rng = random.Random(3)
    for _ in range(300):
        prices = [rng.randint(1, 30) for _ in range(rng.randint(0, 12))]
        assert best_profit(prices) == every_trade(prices)


@pytest.mark.id("tst_zzpyoj")
def test_long():
    """Finds the best trade in a long list in time"""
    rng = random.Random(4)
    prices = [rng.randint(500, 1500) for _ in range(PRICES)]
    prices[PRICES // 3] = 100
    prices[PRICES // 2] = 2000
    assert best_profit(prices) == 1900
