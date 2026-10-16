import pytest

from errors import (
    Failure,
    Number,
    Object,
    String,
    Struct,
    StructError,
    assert_,
    is_,
    validate,
)

SAMPLE = Object({"id": String(), "radius": Number()})


@pytest.mark.id("tst_gc3onr")
def test_assert():
    """Passes superstruct's tests for assert"""
    assert assert_("valid", String()) is None
    with pytest.raises(StructError) as raised:
        assert_(42, String())
    assert isinstance(raised.value, TypeError)
    assert str(raised.value) == "Expected a string, but received: 42"
    assert raised.value.args == ("Expected a string, but received: 42",)


@pytest.mark.id("tst_14z9ec")
def test_path():
    """Explains a failure below the top with its path"""
    author = Object({"author": Object({"name": String()})})
    with pytest.raises(StructError) as raised:
        assert_({"author": {"name": 42}}, author)
    error = raised.value
    assert str(error) == "At path: author.name -- Expected a string, but received: 42"
    assert error.value == 42
    assert error.path == ("author", "name")
    assert error.key == "name"
    assert error.type == "string"
    assert error.refinement is None


@pytest.mark.id("tst_iugykj")
def test_validate():
    """Passes superstruct's tests for validate"""
    assert validate("valid", String()) == (None, "valid")
    error, value = validate(42, String())
    assert value is None
    assert isinstance(error, StructError)
    assert error.failures() == [
        Failure(42, (), "string", "Expected a string, but received: 42")
    ]


@pytest.mark.id("tst_83cfw1")
def test_is():
    """Says whether a value passes"""
    assert is_({"id": "S1", "radius": 17.99}, SAMPLE) is True
    assert is_({"id": "S1", "radius": "x"}, SAMPLE) is False
    assert is_("S1", SAMPLE) is False


@pytest.mark.id("tst_hgjui3")
def test_failures_later():
    """Finds the rest of the failures only when they're asked for, and once"""
    found = []

    class Logged(Object):
        def failures(self, value, path=()):
            for failure in super().failures(value, path):
                found.append(failure.path)
                yield failure

    record = {"id": 1, "radius": "x", "note": "repeat"}
    error, _ = validate(record, Logged({"id": String(), "radius": Number()}))
    assert found == [("id",)]
    assert [failure.path for failure in error.failures()] == [
        ("id",),
        ("radius",),
        ("note",),
    ]
    assert error.failures() is error.failures()
    assert len(found) == 3


@pytest.mark.id("tst_62h1pc")
def test_other_errors():
    """Lets an error the struct raises by mistake through"""

    class Broken(Struct):
        def test(self, value):
            return 1 / 0

    with pytest.raises(ZeroDivisionError):
        validate("S1", Broken())
    with pytest.raises(ZeroDivisionError):
        is_("S1", Broken())
