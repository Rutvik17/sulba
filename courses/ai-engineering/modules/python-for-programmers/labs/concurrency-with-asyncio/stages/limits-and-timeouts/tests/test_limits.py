import pytest

from lookups import Registry, check_in_time, check_limited

KNOWN = {f"S{i:05d}" for i in range(0, 20, 2)}
CODES = [f"S{i:05d}" for i in range(20)]


@pytest.mark.id("tst_2zvjdn")
def test_limited(loop):
    """Makes no more than the limit's lookups at a time, and uses it"""
    registry = Registry(KNOWN)
    checks = loop.run_until_complete(check_limited(CODES, registry, 8))
    assert checks == [
        None if code in KNOWN else f"No patient has the code {code!r}" for code in CODES
    ]
    assert registry.most == 8
    assert loop.time() == 0.75


@pytest.mark.id("tst_rput8w")
def test_limit_of_one(loop):
    """With a limit of 1, makes one lookup after another"""
    registry = Registry(KNOWN)
    loop.run_until_complete(check_limited(CODES[:4], registry, 1))
    assert registry.most == 1
    assert loop.time() == 1.0


@pytest.mark.id("tst_4ydwo2")
def test_in_time(loop):
    """Gives up on a lookup that takes too long"""
    registry = Registry(KNOWN, slow={"S00002": 60})
    assert loop.run_until_complete(check_in_time("S00000", registry, 2)) is None
    assert loop.run_until_complete(check_in_time("S00002", registry, 2)) == (
        "The registry took too long for 'S00002'"
    )
    assert loop.time() == 2.25
    assert registry.serving == 0
