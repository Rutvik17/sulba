import pytest

from day_lookups import Registry, check_code, check_each, check_in_time, check_limited

KNOWN = {"S00001", "S00002", "S00004", "S00005"}
CODES = ["S00001", "S00002", "S00004", "S00005"]


@pytest.mark.id("tst_3avkjc")
def test_check_code(loop):
    """Passes a known code"""
    assert loop.run_until_complete(check_code("S00001", Registry(KNOWN))) is None


@pytest.mark.id("tst_xdj3n7")
def test_limited(loop):
    """Makes no more than the limit's lookups at a time"""
    registry = Registry(KNOWN)
    assert loop.run_until_complete(check_limited(CODES, registry, 2)) == [None] * 4
    assert registry.most == 2
    assert loop.time() == 0.5


@pytest.mark.id("tst_hx2hd4")
def test_each(loop):
    """Makes every lookup at once"""
    registry = Registry(KNOWN)
    assert loop.run_until_complete(check_each(CODES, registry)) == [None] * 4
    assert loop.time() == 0.25


@pytest.mark.id("tst_heo48a")
def test_in_time(loop):
    """Answers every code inside the time"""
    registry = Registry(KNOWN)
    assert loop.run_until_complete(check_in_time(CODES, registry, 2)) == [None] * 4
