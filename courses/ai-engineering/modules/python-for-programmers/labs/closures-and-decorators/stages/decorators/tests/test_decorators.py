import pytest

from refine import counted, define, min_, number, size, string


@pytest.fixture
def code():
    @define("code")
    def code(value):
        """A sample's code: an S, then digits."""
        return isinstance(value, str) and value[:1] == "S" and value[1:].isdigit()

    return code


@pytest.mark.id("tst_r548bw")
def test_define(code):
    """Makes a check from a test, as superstruct's define does"""
    assert code("S00123") is None
    assert code("00123") == "Expected a value of type `code`, but received: `'00123'`"
    assert code(123) == "Expected a value of type `code`, but received: `123`"


@pytest.mark.id("tst_a19qwt")
def test_define_message():
    """Gives a test's own message"""

    @define("side")
    def side(value):
        return value in ("left", "right") or f"No side called {value!r}"

    assert side("left") is None
    assert side("top") == "No side called 'top'"


@pytest.mark.id("tst_u1knmc")
def test_define_names(code):
    """Names the check by its type, and keeps its test's docstring"""
    assert code.__name__ == "code"
    assert code.__doc__ == "A sample's code: an S, then digits."
    assert size(code, 6)("S123") == (
        "Expected a code with a length of `6` but received one with a length of `4`"
    )


@pytest.mark.id("tst_5y9b7i")
def test_counted():
    """Counts the values a check fails"""
    check = counted(number)
    assert check.failed == 0
    assert [check(value) for value in [1, "x", 2.5, None]] == [
        None,
        "Expected a number, but received: 'x'",
        None,
        "Expected a number, but received: None",
    ]
    assert check.failed == 2


@pytest.mark.id("tst_6phacv")
def test_counted_apart():
    """Counts each check apart"""
    radius, texture = counted(number), counted(number)
    radius("x")
    radius("y")
    texture("z")
    assert (radius.failed, texture.failed) == (2, 1)


@pytest.mark.id("tst_xpgtvz")
def test_counted_names():
    """Keeps the check's name and docstring"""
    check = counted(number)
    assert check.__name__ == "number"
    assert check.__doc__ == number.__doc__
    assert (
        min_(check, 5)(2)
        == "Expected a number greater than or equal to 5 but received `2`"
    )


@pytest.mark.id("tst_sk7mzh")
def test_decorator():
    """Counts a check it decorates"""

    @counted
    def side(value):
        return None if value in ("left", "right") else f"No side called {value!r}"

    side("top")
    side("left")
    assert side.failed == 1
    assert side.__name__ == "side"
    assert string("x") is None
