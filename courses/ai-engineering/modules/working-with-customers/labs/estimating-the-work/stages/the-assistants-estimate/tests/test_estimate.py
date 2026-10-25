import pytest

from estimate import estimate
from schedule import OFFICE, Task


@pytest.mark.id("tst_6irj3a")
def test_a_task_that_cant_vary():
    """Promises a fixed task's days, met by any later deadline and missed by an earlier one"""
    assert estimate([Task("only", 4, 4, 4)], 6) == (4, 1.0)
    assert estimate([Task("only", 4, 4, 4)], 3) == (4, 0.0)


@pytest.mark.id("tst_0ym5ym")
def test_the_same_seed():
    """Gives the same estimate for the same seed"""
    assert estimate(OFFICE, 25, seed=1) == estimate(OFFICE, 25, seed=1)


@pytest.mark.id("tst_bh16sc")
def test_later_deadlines():
    """Gives a later deadline no less chance, and every run by the highest days"""
    days, by_25 = estimate(OFFICE, 25)
    _, by_30 = estimate(OFFICE, 30)
    _, by_all = estimate(OFFICE, sum(task.high for task in OFFICE))
    assert 0 <= by_25 <= by_30 <= by_all == 1
    assert days > 0
