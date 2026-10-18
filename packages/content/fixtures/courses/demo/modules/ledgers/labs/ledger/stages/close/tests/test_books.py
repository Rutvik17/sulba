import pytest
from books import close


@pytest.mark.id("tst_demo24")
def test_entries():
    """Counts the entries"""
    assert close([1, 2])["entries"] == 2
