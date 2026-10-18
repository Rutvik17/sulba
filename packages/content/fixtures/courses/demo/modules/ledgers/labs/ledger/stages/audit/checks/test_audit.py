import pytest
from audit import largest


@pytest.mark.id("tst_demo23")
def test_largest():
    assert largest([12, -5, 30]) == 30
