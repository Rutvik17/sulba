import pytest
from stats import mean


@pytest.mark.id("tst_synt01")
def test_mean():
    """The mean of three numbers"""
    assert mean([1, 2, 3]) == 2
