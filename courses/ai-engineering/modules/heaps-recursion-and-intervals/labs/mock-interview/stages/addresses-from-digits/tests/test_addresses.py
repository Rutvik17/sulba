import random
from itertools import combinations

import pytest

from addresses import addresses

DIGITS = 10_000


def every_cut(digits):
    """The addresses, by trying every way to put three dots among the digits."""
    found = []
    for cuts in combinations(range(1, len(digits)), 3):
        numbers = [
            digits[start:end] for start, end in zip((0, *cuts), (*cuts, len(digits)))
        ]
        if all(
            (number == "0" or number[0] != "0") and int(number) <= 255
            for number in numbers
        ):
            found.append(".".join(numbers))
    return sorted(found)


@pytest.mark.id("tst_fm7dy2")
def test_addresses():
    """Gives every address the digits can be"""
    assert addresses("25525511135") == ["255.255.11.135", "255.255.111.35"]
    assert addresses("101023") == [
        "1.0.10.23",
        "1.0.102.3",
        "10.1.0.23",
        "10.10.2.3",
        "101.0.2.3",
    ]


@pytest.mark.id("tst_nebz36")
def test_edges():
    """Handles too few and too many digits, zeros, and numbers over 255"""
    assert addresses("") == []
    assert addresses("123") == []
    assert addresses("0000") == ["0.0.0.0"]
    assert addresses("1111") == ["1.1.1.1"]
    assert addresses("256256256256") == []
    assert addresses("1234567890123") == []


@pytest.mark.id("tst_t42plk")
def test_random():
    """Matches trying every way to put the dots, on random digits"""
    rng = random.Random(611)
    for _ in range(300):
        digits = "".join(rng.choice("01259") for _ in range(rng.randint(0, 13)))
        assert addresses(digits) == every_cut(digits)


@pytest.mark.id("tst_zsfcw0")
def test_long():
    """Gives no address for a long string of digits, in time"""
    assert addresses("1" * DIGITS) == []
