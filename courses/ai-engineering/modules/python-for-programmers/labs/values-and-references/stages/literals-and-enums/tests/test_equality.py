import json

import pytest

from values import enums, literal, same


@pytest.mark.id("tst_wttbz3")
def test_superstruct():
    """Passes superstruct's tests for literal and enums"""
    assert literal(42, 42) is None
    assert literal(False, 42) == "Expected the literal `42`, but received: False"
    assert enums("two", ["one", "two"]) is None
    assert enums("invalid", ["one", "two"]) == (
        "Expected one of `'one','two'`, but received: 'invalid'"
    )
    assert enums("invalid", [1, 2]) == "Expected one of `1,2`, but received: 'invalid'"


@pytest.mark.id("tst_axjai4")
def test_numbers():
    """Compares numbers by value"""
    assert same(42, 42.0)
    assert same(0, -0.0)
    assert same(json.loads("1000"), 1000)
    assert literal(json.loads("1000"), 1000) is None
    assert not same(42, 42.5)


@pytest.mark.id("tst_e0c2b2")
def test_booleans():
    """Never takes a boolean for a number"""
    for a, b in [(True, 1), (1, True), (False, 0), (0.0, False)]:
        assert not same(a, b), (a, b)
    assert same(True, True)
    assert same(False, False)
    assert literal(True, 1) is not None
    assert enums(False, [0, 1]) is not None
    assert enums(1, [0, 1]) is None


@pytest.mark.id("tst_22mwji")
def test_strings():
    """Takes equal strings, wherever they came from"""
    assert same(json.loads('"malignant"'), "malignant")
    assert literal("".join(["mali", "gnant"]), "malignant") is None
    assert not same("1", 1)
    assert not same("", None)


@pytest.mark.id("tst_6ttrua")
def test_objects():
    """Compares lists and dicts as the same object"""
    sample = {"id": "842302"}
    assert same(sample, sample)
    assert not same({"id": "842302"}, sample)
    assert not same([1], [1])
    assert literal(sample, sample) is None
    assert literal(dict(sample), sample) is not None


@pytest.mark.id("tst_sg0rvx")
def test_none():
    """Tells None from other falsy values"""
    assert same(None, None)
    for value in [0, "", False, [], {}]:
        assert not same(None, value), value
        assert not same(value, None), value


@pytest.mark.id("tst_ldxdos")
def test_nan():
    """Never equals NaN, but finds it among the options"""
    nan = json.loads("NaN")
    assert not same(nan, nan)
    assert literal(nan, nan) is not None
    assert enums(json.loads("NaN"), [1, float("nan")]) is None
    assert enums(nan, [1, 2]) is not None
