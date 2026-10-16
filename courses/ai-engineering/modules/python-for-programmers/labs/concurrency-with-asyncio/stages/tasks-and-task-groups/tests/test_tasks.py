import pytest

from lookups import Registry, check_all, check_at_once, check_each

KNOWN = {"S00001", "S00002", "S00004"}
CODES = ["S00001", "S00002", "S00003", "S00004"]
CHECKS = [None, None, "No patient has the code 'S00003'", None]


@pytest.mark.id("tst_ro73lc")
def test_at_once(loop):
    """Makes every lookup at once"""
    registry = Registry(KNOWN)
    assert loop.run_until_complete(check_at_once(CODES, registry)) == CHECKS
    assert registry.most == 4
    assert loop.time() == 0.25


@pytest.mark.id("tst_zhh35w")
def test_all(loop):
    """Makes every lookup at once in a task group"""
    registry = Registry(KNOWN)
    assert loop.run_until_complete(check_all(CODES, registry)) == CHECKS
    assert registry.most == 4
    assert loop.time() == 0.25


@pytest.mark.id("tst_xltg6c")
def test_all_cancels(loop):
    """Cancels the lookups still waiting when one fails"""
    registry = Registry(KNOWN, slow={"S00004": 60}, failing={"S00002"})
    with pytest.raises(ExceptionGroup) as raised:
        loop.run_until_complete(check_all(CODES, registry))
    assert [type(error) for error in raised.value.exceptions] == [ConnectionError]
    assert loop.time() == 0.25
    assert registry.serving == 0


@pytest.mark.id("tst_26azq8")
def test_each(loop):
    """Reports a lookup that couldn't reach the registry, and keeps the rest"""
    registry = Registry(KNOWN, failing={"S00002"})
    assert loop.run_until_complete(check_each(CODES, registry)) == [
        None,
        "The registry couldn't be reached for 'S00002'",
        "No patient has the code 'S00003'",
        None,
    ]
    assert loop.time() == 0.25
