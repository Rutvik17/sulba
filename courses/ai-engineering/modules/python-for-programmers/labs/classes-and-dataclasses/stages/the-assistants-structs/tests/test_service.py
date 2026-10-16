import pytest

from service import Enums, Failure, Number, Object, String, Union


@pytest.mark.id("tst_zfwuvx")
def test_kinds():
    """Passes strings and numbers, and fails the rest"""
    assert String().validate("S1") is None
    assert Number().validate(17.99) is None
    assert Number().validate("17.99") == Failure(
        (), "number", "Expected a number, but received: '17.99'"
    )


@pytest.mark.id("tst_01u3za")
def test_message():
    """Fails a value with the clinic's message, where a struct has one"""
    code = String(message="Give the sample's code as text.")
    assert code.validate(842302).message == "Give the sample's code as text."
    assert (
        String().validate(842302).message == "Expected a string, but received: 842302"
    )


@pytest.mark.id("tst_l0ck6b")
def test_enums():
    """Passes the options and fails the rest"""
    side = Enums(["left", "right"])
    assert "left" in side
    assert side.validate("top").message == (
        "Expected one of `'left','right'`, but received: 'top'"
    )


@pytest.mark.id("tst_w5ilry")
def test_object():
    """Reports each field's failure, at its path"""
    sample = Object({"id": String(), "radius": Number()})
    assert {"id": "S1", "radius": 17.99} in sample
    assert list(sample.failures({"id": "S1", "radius": "x", "note": 1})) == [
        Failure(("radius",), "number", "Expected a number, but received: 'x'"),
        Failure(
            ("note",), "never", "Expected a value of type `never`, but received: `1`"
        ),
    ]


@pytest.mark.id("tst_ph7g78")
def test_union():
    """Joins structs with a bar"""
    either = String() | Number() | Object({})
    assert isinstance(either, Union)
    assert len(either.members) == 3
    assert "S1" in either
    assert 42 in either
    assert either.validate(True).message == (
        "Expected the value to satisfy a union of `string | number | object`, "
        "but received: True"
    )
