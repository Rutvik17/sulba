import pytest
from tally import share


@pytest.mark.id("tst_demo03")
def test_share():
    """Two of three votes for yes"""
    assert share(["yes", "no", "yes"], "yes") == pytest.approx(2 / 3)
