import random
from itertools import permutations

import pytest
from largest_number import largest_number

NUMBERS = 2_000


def every_order(numbers):
    """The largest number, by writing the numbers in every order."""
    best = max("".join(map(str, order)) for order in permutations(numbers))
    return best.lstrip("0") or "0"


def by_repeating(numbers):
    """The largest number, sorting each number by its digits repeated to twice the longest.

    Two numbers' orders compare as their digits repeated forever do, and two such repeats
    that agree for as many digits as the two numbers have together agree for good.
    """
    texts = [str(number) for number in numbers]
    width = 2 * max(map(len, texts))
    order = sorted(texts, key=lambda text: (text * width)[:width], reverse=True)
    return "".join(order).lstrip("0") or "0"


@pytest.mark.id("tst_tveirq")
def test_largest():
    """Writes the numbers in the order that makes the largest number"""
    assert largest_number([7, 75, 761, 2]) == "7761752"


@pytest.mark.id("tst_851ims")
def test_order():
    """Puts 3 before 30 and 2 before 10, and gives "0" for zeros"""
    assert largest_number([3, 30, 34]) == "34330"
    assert largest_number([10, 2]) == "210"
    assert largest_number([0, 0]) == "0"
    assert largest_number([5]) == "5"


@pytest.mark.id("tst_6dw0d7")
def test_every_order():
    """Matches writing the numbers in every order"""
    rng = random.Random(62)
    for _ in range(300):
        numbers = [
            rng.choice([0, 1, 3, 30, 34, 5, 9, 90, 98])
            for _ in range(rng.randint(1, 6))
        ]
        assert largest_number(numbers) == every_order(numbers)


@pytest.mark.id("tst_7g5zpz")
def test_long():
    """Orders many numbers in time"""
    rng = random.Random(63)
    numbers = [rng.randint(0, 9999) for _ in range(NUMBERS)]
    assert largest_number(numbers) == by_repeating(numbers)
