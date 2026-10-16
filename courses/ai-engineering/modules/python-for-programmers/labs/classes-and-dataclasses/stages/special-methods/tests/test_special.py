import pytest

from structs import Array, Failure, Number, Object, String, Type, Union


@pytest.mark.id("tst_uhgc1q")
def test_bar():
    """Joins two structs with a bar"""
    string, number = String(), Number()
    either = string | number
    assert isinstance(either, Union)
    assert either.members == (string, number)
    assert either.validate("S1") is None
    assert either.validate(42) is None


@pytest.mark.id("tst_m49enq")
def test_union():
    """Passes superstruct's tests for union"""
    either = Type({"a": String()}) | Type({"b": Number()})
    assert list(either.failures({"a": "a"})) == []
    assert list(either.failures({"b": "invalid"})) == [
        Failure(
            (),
            "union",
            "Expected the value to satisfy a union of `type | type`, "
            "but received: {'b': 'invalid'}",
        ),
        Failure(("a",), "string", "Expected a string, but received: undefined"),
        Failure(("b",), "number", "Expected a number, but received: 'invalid'"),
    ]


@pytest.mark.id("tst_ddr0lq")
def test_many():
    """Joins any number of structs into one union"""
    string, number, strings = String(), Number(), Array(String())
    joined = (string | number) | strings
    assert joined.members == (string, number, strings)
    assert (string | (number | strings)).members == (string, number, strings)
    assert joined.validate(True).message == (
        "Expected the value to satisfy a union of `string | number | array`, "
        "but received: True"
    )


@pytest.mark.id("tst_mg6955")
def test_only_structs():
    """Joins only structs"""
    with pytest.raises(TypeError):
        String() | 42
    with pytest.raises(TypeError):
        "S1" | Number()


@pytest.mark.id("tst_cs7qfx")
def test_in():
    """Answers whether a value passes, with in"""
    assert 42 in Number()
    assert "42" not in Number()
    sample = Object({"id": String(), "radius": Number()})
    assert {"id": "S1", "radius": 17.99} in sample
    assert {"id": "S1"} not in sample


@pytest.mark.id("tst_dnudoc")
def test_fields():
    """Gives an object's struct for a field"""
    name = String()
    person = Type({"name": name, "age": Number()})
    assert person["name"] is name
    with pytest.raises(KeyError):
        person["height"]


@pytest.mark.id("tst_m1x9ub")
def test_repr():
    """Shows each struct as it's made"""
    sample = Object({"id": String(), "tags": Array(String())})
    assert repr(sample) == "Object({'id': String(), 'tags': Array(String())})"
    assert repr(Type({})) == "Type({})"
    assert repr(String() | Number()) == "String() | Number()"
