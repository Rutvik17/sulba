import pytest
from books import close


@pytest.mark.id("tst_demo25")
def test_balance(record_property):
    closed = close([12, -5, 30])
    record_property("note", f"closes at {closed['balance']}")
    assert closed["balance"] == 37
