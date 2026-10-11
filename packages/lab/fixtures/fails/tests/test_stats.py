import pytest
from stats import mean, middle


@pytest.mark.id("tst_fail01")
def test_mean():
    """The mean of three numbers"""
    assert mean([1, 2, 3]) == 2


@pytest.mark.id("tst_fail02")
def test_even_count():
    """An even count takes the mean of the two middle values"""
    assert middle([1, 2, 3, 4]) == pytest.approx(2.5), "The middle of 1, 2, 3 and 4 is 2.5"


@pytest.mark.id("tst_fail03")
def test_empty():
    """No values"""
    with pytest.raises(ValueError):
        mean([])
