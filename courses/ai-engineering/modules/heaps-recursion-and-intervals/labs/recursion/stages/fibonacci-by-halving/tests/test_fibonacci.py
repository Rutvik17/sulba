import random

import pytest

from fibonacci import fibonacci

LARGEST = 10**18


def by_adding(n):
    """F(n), by adding the numbers up one at a time."""
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return a


def by_matrix(n, modulus):
    """F(n) mod modulus, from the matrix [[1, 1], [1, 0]] raised to the nth power by squaring."""

    def times(x, y):
        return [
            [
                (x[0][0] * y[0][0] + x[0][1] * y[1][0]) % modulus,
                (x[0][0] * y[0][1] + x[0][1] * y[1][1]) % modulus,
            ],
            [
                (x[1][0] * y[0][0] + x[1][1] * y[1][0]) % modulus,
                (x[1][0] * y[0][1] + x[1][1] * y[1][1]) % modulus,
            ],
        ]

    found, power = [[1 % modulus, 0], [0, 1 % modulus]], [[1, 1], [1, 0]]
    while n:
        if n % 2:
            found = times(found, power)
        power = times(power, power)
        n //= 2
    return found[0][1]


@pytest.mark.id("tst_nolw7v")
def test_fibonacci():
    """Gives a Fibonacci number mod the modulus"""
    assert fibonacci(10, 1000) == 55
    assert fibonacci(100, 1_000_000_007) == by_adding(100) % 1_000_000_007


@pytest.mark.id("tst_kw97zu")
def test_edges():
    """Gives F(0) and F(1), and 0 for a modulus of 1"""
    assert fibonacci(0, 10) == 0
    assert fibonacci(1, 10) == 1
    assert fibonacci(2, 10) == 1
    assert fibonacci(1, 1) == 0
    assert fibonacci(50, 1) == 0


@pytest.mark.id("tst_1c621u")
def test_random():
    """Matches adding the numbers up, for random n and moduli"""
    rng = random.Random(311)
    numbers = [by_adding(n) for n in range(2_000)]
    for _ in range(500):
        n, modulus = rng.randrange(2_000), rng.randint(1, 10**12)
        assert fibonacci(n, modulus) == numbers[n] % modulus


@pytest.mark.id("tst_1qg0kx")
def test_long():
    """Gives F(n) for n up to 10 ** 18 in time"""
    rng = random.Random(312)
    assert fibonacci(LARGEST, 1_000_000_007) == by_matrix(LARGEST, 1_000_000_007)
    for _ in range(300):
        n, modulus = rng.randint(0, LARGEST), rng.randint(1, LARGEST)
        assert fibonacci(n, modulus) == by_matrix(n, modulus)
