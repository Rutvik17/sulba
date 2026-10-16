import re

import pytest

from refine import max_, min_, number, pattern, refine, string


@pytest.mark.id("tst_whl7d6")
def test_refine():
    """Passes superstruct's tests for refine"""
    email = refine(string, "email", lambda value: "@" in value)
    assert email("name@example.com") is None
    assert email("invalid") == (
        "Expected a value of type `string` with refinement `email`, "
        "but received: `'invalid'`"
    )
    positive = refine(number, "positive", lambda v: v > 0 or "Number was not positive!")
    assert positive(1) is None
    assert positive(-1) == "Number was not positive!"


@pytest.mark.id("tst_1hanig")
def test_check_first():
    """Tests only a value the check passes"""

    def test(value):
        if not isinstance(value, (int, float)):
            raise TypeError("The test was given a value its check had failed.")
        return value > 0

    positive = refine(number, "positive", test)
    assert positive("x") == "Expected a number, but received: 'x'"
    assert min_(number, 0)("x") == "Expected a number, but received: 'x'"
    assert (
        pattern(string, re.compile(r"\d+"))(42) == "Expected a string, but received: 42"
    )


@pytest.mark.id("tst_1dgrnx")
def test_true_only():
    """Passes a value only when the test gives True"""
    check = refine(string, "found", lambda value: value.find("@"))
    assert check("a@b") is not None
    assert check("@ab") is not None


@pytest.mark.id("tst_laclj9")
def test_min():
    """Passes superstruct's tests for min"""
    check = min_(number, 0)
    assert check(3) is None
    assert check(0) is None
    assert check(-1) == "Expected a number greater than or equal to 0 but received `-1`"
    exclusive = min_(number, 0, exclusive=True)
    assert exclusive(0) == "Expected a number greater than 0 but received `0`"
    assert exclusive(0.5) is None


@pytest.mark.id("tst_othojr")
def test_max():
    """Passes superstruct's tests for max"""
    check = max_(number, 0)
    assert check(-1) is None
    assert check(0) is None
    assert check(1) == "Expected a number less than or equal to 0 but received `1`"
    assert max_(number, 0, exclusive=True)(0) == (
        "Expected a number less than 0 but received `0`"
    )


@pytest.mark.id("tst_dyg8do")
def test_pattern():
    """Passes superstruct's tests for pattern"""
    check = pattern(string, re.compile(r"\d+"))
    assert check("123") is None
    assert check("S123") is None
    assert (
        check("invalid") == "Expected a string matching `/\\d+/` but received 'invalid'"
    )


@pytest.mark.id("tst_42ue4e")
def test_stacked():
    """Applies refinements on top of each other"""
    radius = min_(max_(number, 30), 5)
    assert radius(17.99) is None
    assert radius(40) == "Expected a number less than or equal to 30 but received `40`"
    assert radius(2) == "Expected a number greater than or equal to 5 but received `2`"
    assert radius("x") == "Expected a number, but received: 'x'"
    assert radius.__name__ == "number"
