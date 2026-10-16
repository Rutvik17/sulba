import pytest

from refine import cached, number


def logged(check):
    """check, and the list of values it's called with."""
    calls = []

    def logging(value):
        calls.append(value)
        return check(value)

    logging.__name__ = check.__name__
    logging.__doc__ = check.__doc__
    return logging, calls


@pytest.mark.id("tst_g0n17v")
def test_messages():
    """Gives the check's own messages"""
    check = cached(16)(number)
    for value in [1, "x", 2.5, None, float("nan"), "x", 1]:
        assert check(value) == number(value)


@pytest.mark.id("tst_wk9khw")
def test_once():
    """Calls the check once for each value it keeps"""
    check, calls = logged(number)
    check = cached(16)(check)
    for value in ["S1", "S2", "S1", "S1", "S3", "S2"]:
        check(value)
    assert calls == ["S1", "S2", "S3"]


@pytest.mark.id("tst_8j8y2m")
def test_names():
    """Keeps the check's name and docstring"""
    check = cached(16)(number)
    assert check.__name__ == "number"
    assert check.__doc__ == number.__doc__


@pytest.mark.id("tst_cderjv")
def test_unhashable():
    """Checks lists and dicts each time"""
    check, calls = logged(number)
    check = cached(16)(check)
    assert check([1]) == "Expected a number, but received: [1]"
    assert check([1]) == "Expected a number, but received: [1]"
    assert check({"a": 1}) == "Expected a number, but received: {'a': 1}"
    assert calls == [[1], [1], {"a": 1}]


@pytest.mark.id("tst_ibb0fe")
def test_decorator():
    """Works as a decorator"""

    @cached(4)
    def side(value):
        return None if value in ("left", "right") else f"No side called {value!r}"

    assert side("top") == "No side called 'top'"
    assert side("left") is None
    assert side.__name__ == "side"
