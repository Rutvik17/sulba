import json
import math

import pytest

from values import boolean, integer, number, string


@pytest.mark.id("tst_mt3rlz")
def test_superstruct():
    """Passes superstruct's tests for these checks"""
    # Its fixtures in test/validation: valid.ts and invalid.ts for each check.
    assert string("valid") is None
    assert string(False) == "Expected a string, but received: False"
    assert number(42) is None
    assert number("invalid") == "Expected a number, but received: 'invalid'"
    assert integer(42) is None
    assert integer(3.14) == "Expected an integer, but received: 3.14"
    assert integer("invalid") == "Expected an integer, but received: 'invalid'"
    assert boolean(True) is None
    assert boolean("invalid") == (
        "Expected a value of type `boolean`, but received: `'invalid'`"
    )


@pytest.mark.id("tst_4javbh")
def test_floats():
    """Takes ints and floats as numbers"""
    for value in [0, -7, 4.2, -0.0, json.loads("1e-5")]:
        assert number(value) is None, value


@pytest.mark.id("tst_qs708v")
def test_booleans_are_not_numbers():
    """Takes no boolean for a number"""
    for check in [number, integer]:
        for value in [True, False]:
            assert check(value) is not None, (check.__name__, value)
    assert number(True) == "Expected a number, but received: True"


@pytest.mark.id("tst_jcou0r")
def test_nan():
    """Takes no NaN for a number"""
    nan = json.loads("NaN")
    assert number(nan) == "Expected a number, but received: nan"
    assert integer(nan) == "Expected an integer, but received: nan"


@pytest.mark.id("tst_ujlmir")
def test_infinity():
    """Takes infinity for a number, not an integer"""
    for value in [math.inf, -math.inf]:
        assert number(value) is None
        assert integer(value) is not None


@pytest.mark.id("tst_phex4h")
def test_whole_floats():
    """Takes a float with no fraction for an integer"""
    for value in [json.loads("3.0"), -0.0, 2.0**60]:
        assert integer(value) is None, value
    assert integer(json.loads("3.5")) == "Expected an integer, but received: 3.5"


@pytest.mark.id("tst_klavpq")
def test_large_ints():
    """Takes an int of any size"""
    huge = json.loads("1" + "0" * 400)
    assert number(huge) is None
    assert integer(huge) is None


@pytest.mark.id("tst_i58upa")
def test_strings_are_not_numbers():
    """Takes no string for a number"""
    for value in ["42", "", "NaN"]:
        assert number(value) is not None, value
        assert integer(value) is not None, value
    assert string(42) == "Expected a string, but received: 42"
    assert string(None) == "Expected a string, but received: None"


@pytest.mark.id("tst_yf8b3u")
def test_booleans():
    """Takes only True and False for booleans"""
    assert boolean(False) is None
    for value in [0, 1, None, "true", [], "False"]:
        assert boolean(value) is not None, value
