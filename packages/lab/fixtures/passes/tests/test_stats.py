import pytest
from stats import mean


@pytest.mark.id("tst_pass01")
def test_whole_numbers():
    """The mean of whole numbers"""
    assert mean([1, 2, 3]) == 2


@pytest.mark.id("tst_pass02")
def test_fractions():
    """The mean of fractions"""
    assert mean([0.1, 0.2]) == pytest.approx(0.15)
