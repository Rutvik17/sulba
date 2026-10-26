import random

import pytest

from kth import KthLargest

K = 1_000
ADDS = 200_000


@pytest.mark.id("tst_5v285a")
def test_kth_largest():
    """Gives the kth largest after each number"""
    stream = KthLargest(3, [4, 5, 8, 2])
    assert [stream.add(number) for number in [3, 5, 10, 9, 4]] == [4, 5, 5, 8, 8]


@pytest.mark.id("tst_x8ayza")
def test_edges():
    """Starts with k - 1 numbers, counts a repeat twice, and takes k of 1"""
    stream = KthLargest(2, [7])
    assert stream.add(3) == 3
    assert stream.add(7) == 7
    one = KthLargest(1, [])
    assert [one.add(number) for number in [-5, -9, 2, 2]] == [-5, -5, 2, 2]


@pytest.mark.id("tst_zizngy")
def test_random():
    """Matches sorting every number so far, on random streams"""
    rng = random.Random(231)
    for _ in range(200):
        k = rng.randint(1, 6)
        numbers = [rng.randint(-20, 20) for _ in range(rng.randint(k - 1, k + 5))]
        stream = KthLargest(k, list(numbers))
        for _ in range(rng.randint(1, 15)):
            number = rng.randint(-20, 20)
            numbers.append(number)
            assert stream.add(number) == sorted(numbers)[-k]


@pytest.mark.id("tst_csw43c")
def test_long():
    """Gives the kth largest of a long stream in time"""
    rng = random.Random(232)
    numbers = [rng.randint(0, 10**9) for _ in range(K - 1)]
    stream = KthLargest(K, numbers)
    added = [rng.randint(0, 10**9) for _ in range(ADDS)]
    for number in added:
        last = stream.add(number)
    assert last == sorted(numbers + added)[-K]
