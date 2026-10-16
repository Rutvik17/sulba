import pytest

from lookups import Registry, check_day

KNOWN = {f"S{i:05d}" for i in range(12) if i % 3}
CODES = [f"S{i:05d}" for i in range(12)]


@pytest.mark.id("tst_u060ir")
def test_checks(loop):
    """Checks each code, in order"""
    registry = Registry(KNOWN)
    assert loop.run_until_complete(check_day(CODES, registry, 3, 5)) == [
        None if code in KNOWN else f"No patient has the code {code!r}" for code in CODES
    ]
    assert loop.run_until_complete(check_day([], registry, 3, 5)) == []


@pytest.mark.id("tst_01172n")
def test_dropped(loop):
    """Gives a dropped lookup its own message"""
    registry = Registry(KNOWN, failing={"S00002"})
    assert loop.run_until_complete(check_day(CODES[:4], registry, 2, 5)) == [
        "No patient has the code 'S00000'",
        None,
        "The registry couldn't be reached for 'S00002'",
        "No patient has the code 'S00003'",
    ]


@pytest.mark.id("tst_62h27t")
def test_slow(loop):
    """Gives a slow lookup its own message"""
    registry = Registry(KNOWN, slow={"S00001": 60})
    assert loop.run_until_complete(check_day(CODES[:4], registry, 4, 2)) == [
        "No patient has the code 'S00000'",
        "The registry took too long for 'S00001'",
        None,
        "No patient has the code 'S00003'",
    ]
    assert registry.serving == 0
