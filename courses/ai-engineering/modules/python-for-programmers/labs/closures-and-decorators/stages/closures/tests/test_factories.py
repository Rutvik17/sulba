import json

import pytest

from refine import enums, literal, nullable, number, size, string


@pytest.mark.id("tst_abxqmw")
def test_literal():
    """Passes superstruct's tests for literal"""
    check = literal(42)
    assert check(42) is None
    assert check(False) == "Expected the literal `42`, but received: False"
    assert check(json.loads("42.0")) is None


@pytest.mark.id("tst_5qomps")
def test_enums():
    """Passes superstruct's tests for enums"""
    check = enums(["one", "two"])
    assert check("two") is None
    assert check("invalid") == "Expected one of `'one','two'`, but received: 'invalid'"
    assert enums([1, 2])("invalid") == "Expected one of `1,2`, but received: 'invalid'"
    assert enums([0, 1])(True) is not None


@pytest.mark.id("tst_ifujye")
def test_each_its_own():
    """Makes each check with its own constant"""
    checks = [literal(side) for side in ["left", "right", "both"]]
    assert [check("right") for check in checks] == [
        "Expected the literal `'left'`, but received: 'right'",
        None,
        "Expected the literal `'both'`, but received: 'right'",
    ]


@pytest.mark.id("tst_bj52i5")
def test_options_kept():
    """Keeps the options it was made with"""
    sides = ["left", "right"]
    check = enums(sides)
    sides.append("both")
    assert check("both") == "Expected one of `'left','right'`, but received: 'both'"
    assert check("left") is None


@pytest.mark.id("tst_2qc3bo")
def test_nullable():
    """Passes superstruct's tests for nullable"""
    check = nullable(number)
    assert check(42) is None
    assert check(None) is None
    assert check("invalid") == "Expected a number, but received: 'invalid'"


@pytest.mark.id("tst_ggo5kg")
def test_size_numbers():
    """Passes superstruct's tests for the size of a number"""
    check = size(number, 1, 5)
    assert check(3) is None
    assert check(1) is None and check(5) is None
    assert check(0) == "Expected a number between `1` and `5` but received `0`"
    assert check(5.5) == "Expected a number between `1` and `5` but received `5.5`"


@pytest.mark.id("tst_625kpa")
def test_size_strings():
    """Passes superstruct's tests for the size of a string"""
    check = size(string, 1, 5)
    assert check("two") is None
    assert check("a") is None and check("abcde") is None
    assert check("") == (
        "Expected a string with a length between `1` and `5` "
        "but received one with a length of `0`"
    )
    assert size(string, 4)("abcd") is None
    assert size(string, 4)("abc") == (
        "Expected a string with a length of `4` but received one with a length of `3`"
    )


@pytest.mark.id("tst_2b6x0i")
def test_size_checks_first():
    """Gives the check's own message before measuring"""
    assert size(number, 1, 5)("three") == "Expected a number, but received: 'three'"
    assert size(string, 1, 5)(None) == "Expected a string, but received: None"
