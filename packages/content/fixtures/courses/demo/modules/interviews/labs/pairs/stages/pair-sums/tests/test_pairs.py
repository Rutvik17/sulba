import pytest
from pairs import pair_sum


@pytest.mark.id("tst_demo13")
def test_pair():
    """Finds the two numbers that add up to the target"""
    assert pair_sum([3, 9, 4, 7], 11) == (2, 3)


@pytest.mark.id("tst_demo14")
def test_no_pair():
    """Returns None when no two numbers add up to the target"""
    assert pair_sum([1, 2, 4], 9) is None
    assert pair_sum([5, 1], 10) is None


@pytest.mark.id("tst_demo15")
def test_long_list():
    """Finds the pair in a hundred thousand numbers in time"""
    numbers = [2 * each for each in range(99_999)] + [1]
    assert pair_sum(numbers, 2 * 99_998 + 1) == (99_998, 99_999)
