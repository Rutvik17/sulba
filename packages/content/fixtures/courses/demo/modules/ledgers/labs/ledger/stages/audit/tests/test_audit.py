import pytest
from audit import report


@pytest.mark.id("tst_demo22")
def test_report():
    """Reports the balance and the largest entry"""
    assert report([4]) == {"balance": 4, "largest": 4}
