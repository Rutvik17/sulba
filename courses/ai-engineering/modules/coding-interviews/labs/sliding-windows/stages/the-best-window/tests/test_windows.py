import random

import pytest
from windows import best_window

NUMBERS = 100_000
WIDTH = 50_000


def every_window(numbers, k):
    """The largest sum of k adjacent numbers, summing each window afresh."""
    return max(sum(numbers[i : i + k]) for i in range(len(numbers) - k + 1))


@pytest.mark.id("tst_0i3xzt")
def test_window():
    """Finds the window with the largest sum"""
    assert best_window([4, -2, 7, 1, -5, 6, 3], 3) == 9


@pytest.mark.id("tst_pmyec0")
def test_edges():
    """Handles a window of one, a window of the whole list, and negative numbers"""
    assert best_window([3, 9, 2], 1) == 9
    assert best_window([3, 9, 2], 3) == 14
    assert best_window([-4, -1, -3], 2) == -4


@pytest.mark.id("tst_ima4yf")
def test_every_window():
    """Matches summing every window afresh"""
    rng = random.Random(34)
    for _ in range(300):
        numbers = [rng.randint(-9, 9) for _ in range(rng.randint(1, 12))]
        k = rng.randint(1, len(numbers))
        assert best_window(numbers, k) == every_window(numbers, k)


@pytest.mark.id("tst_ge8sep")
def test_long():
    """Finds the best wide window in a long list in time"""
    rng = random.Random(35)
    numbers = [rng.randint(-100, 100) for _ in range(NUMBERS)]
    numbers[20_000 : 20_000 + WIDTH] = [1000] * WIDTH
    assert best_window(numbers, WIDTH) == 1000 * WIDTH
