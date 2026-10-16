import pytest

from day_lookups import Registry, check_code, check_each, check_in_time, check_limited

KNOWN = {"S00001", "S00002", "S00004", "S00005"}
CODES = ["S00001", "S00002", "S00004", "S00005", "S00007", "S00008"]


@pytest.mark.id("tst_xy2uiw")
def test_unknown(loop):
    """Fails a code the registry doesn't know"""
    registry = Registry(KNOWN)
    assert loop.run_until_complete(check_code("S00003", registry)) == (
        "No patient has the code 'S00003'"
    )
    assert registry.asked == ["S00003"]


@pytest.mark.id("tst_9oq1ly")
def test_limited_after_failures(loop):
    """Keeps to its limit after lookups that couldn't reach the registry"""
    registry = Registry(KNOWN, failing={"S00001", "S00002"})
    checks = loop.run_until_complete(check_limited(CODES, registry, 2))
    assert checks == [
        "The registry couldn't be reached for 'S00001'",
        "The registry couldn't be reached for 'S00002'",
        None,
        None,
        "No patient has the code 'S00007'",
        "No patient has the code 'S00008'",
    ]
    assert registry.most == 2


@pytest.mark.id("tst_u2b9x6")
def test_each_failure_alone(loop):
    """Keeps a lookup that couldn't reach the registry to its own code"""
    registry = Registry(KNOWN, failing={"S00002"})
    assert loop.run_until_complete(check_each(CODES[:4], registry)) == [
        None,
        "The registry couldn't be reached for 'S00002'",
        None,
        None,
    ]


@pytest.mark.id("tst_pmlwzg")
def test_slow_alone(loop):
    """Times out a slow lookup without the others"""
    registry = Registry(KNOWN, slow={"S00004": 60})
    assert loop.run_until_complete(check_in_time(CODES[:4], registry, 2)) == [
        None,
        None,
        "The registry took too long for 'S00004'",
        None,
    ]
    assert loop.time() == 2
