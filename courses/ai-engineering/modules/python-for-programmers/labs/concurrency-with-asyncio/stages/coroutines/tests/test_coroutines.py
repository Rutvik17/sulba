import asyncio

import pytest

from lookups import Registry, check_code, check_codes, first_unknown

KNOWN = {"S00001", "S00002", "S00004"}


@pytest.mark.id("tst_y0ka3p")
def test_check_code(loop):
    """Passes a known code and names an unknown one"""
    registry = Registry(KNOWN)
    assert loop.run_until_complete(check_code("S00001", registry)) is None
    assert loop.run_until_complete(check_code("S00003", registry)) == (
        "No patient has the code 'S00003'"
    )
    assert loop.time() == 0.5


@pytest.mark.id("tst_ffbfcq")
def test_lazy(loop):
    """Asks the registry nothing until the check is awaited"""
    registry = Registry(KNOWN)
    check = check_code("S00001", registry)
    assert asyncio.iscoroutine(check)
    assert registry.asked == []
    loop.run_until_complete(check)
    assert registry.asked == ["S00001"]


@pytest.mark.id("tst_8rs89y")
def test_check_codes(loop):
    """Checks each code in order, one lookup after another"""
    registry = Registry(KNOWN)
    codes = ["S00001", "S00002", "S00003", "S00004"]
    assert loop.run_until_complete(check_codes(codes, registry)) == [
        None,
        None,
        "No patient has the code 'S00003'",
        None,
    ]
    assert registry.asked == codes
    assert registry.most == 1
    assert loop.time() == 1.0


@pytest.mark.id("tst_34022y")
def test_first_unknown(loop):
    """Stops at the first code the registry doesn't know"""
    registry = Registry(KNOWN)
    found = loop.run_until_complete(
        first_unknown(["S00001", "S00003", "S00002"], registry)
    )
    assert found == "S00003"
    assert registry.asked == ["S00001", "S00003"]
    assert loop.run_until_complete(first_unknown(["S00004"], registry)) is None
