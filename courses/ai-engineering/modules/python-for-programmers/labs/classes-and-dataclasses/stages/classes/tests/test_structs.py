import pytest

from structs import Array, Failure, Number, Object, String, Struct, Type


def found(struct, value):
    return list(struct.failures(value))


@pytest.mark.id("tst_kwo75y")
def test_kinds():
    """Makes each kind of struct a Struct"""
    for struct in [String(), Number(), Object({}), Array(Number()), Type({})]:
        assert isinstance(struct, Struct)
    assert isinstance(Type({}), Object)


@pytest.mark.id("tst_vjz3fe")
def test_objects():
    """Passes superstruct's tests for objects"""
    person = Object({"name": String(), "age": Number()})
    assert found(person, {"name": "john", "age": 42}) == []
    assert found(person, "invalid") == [
        Failure((), "object", "Expected an object, but received: 'invalid'")
    ]
    assert found(Object({}), []) == [
        Failure((), "object", "Expected an object, but received: []")
    ]
    tall = Object({"name": String(), "age": Number(), "height": String()})
    assert found(tall, {"name": "john", "age": "invalid", "height": 2}) == [
        Failure(("age",), "number", "Expected a number, but received: 'invalid'"),
        Failure(("height",), "string", "Expected a string, but received: 2"),
    ]
    assert found(person, {"name": "john", "age": 42, "unknown": True}) == [
        Failure(
            ("unknown",),
            "never",
            "Expected a value of type `never`, but received: `True`",
        )
    ]


@pytest.mark.id("tst_53vbb2")
def test_arrays():
    """Passes superstruct's tests for arrays"""
    assert found(Array(Number()), [1, 2, 3]) == []
    assert found(Array(Number()), [1, "invalid", 3]) == [
        Failure((1,), "number", "Expected a number, but received: 'invalid'")
    ]
    assert found(Array(Number()), "invalid") == [
        Failure((), "array", "Expected an array value, but received: 'invalid'")
    ]


@pytest.mark.id("tst_vlwayj")
def test_nested():
    """Passes superstruct's tests for nested structs"""
    person = Object({"name": String(), "emails": Array(String())})
    assert found(person, {"name": "john", "emails": ["name@example.com", False]}) == [
        Failure(("emails", 1), "string", "Expected a string, but received: False")
    ]
    people = Array(Object({"id": String()}))
    assert found(people, [{"id": "1"}, {"id": False}, {"id": "3"}]) == [
        Failure((1, "id"), "string", "Expected a string, but received: False")
    ]


@pytest.mark.id("tst_nxzbyn")
def test_types():
    """Passes superstruct's tests for type, which lets unknown fields pass"""
    person = Type({"name": String(), "age": Number()})
    assert found(person, {"name": "john", "age": 42, "unknown": True}) == []
    assert found(person, {"name": "john", "age": "invalid"}) == [
        Failure(("age",), "number", "Expected a number, but received: 'invalid'")
    ]
    assert found(person, "invalid") == [
        Failure((), "type", "Expected an object, but received: 'invalid'")
    ]
    nested = Type({"id": Number(), "person": Type({"name": String()})})
    assert found(nested, {"id": 1}) == [
        Failure(("person",), "type", "Expected an object, but received: undefined")
    ]


@pytest.mark.id("tst_jjwr4n")
def test_missing():
    """Gives a field the value leaves out as undefined"""
    assert found(Object({"id": String()}), {}) == [
        Failure(("id",), "string", "Expected a string, but received: undefined")
    ]


@pytest.mark.id("tst_bpp67v")
def test_validate():
    """Gives the first failure, or None"""
    person = Object({"name": String(), "age": Number()})
    assert person.validate({"name": 1, "age": "x"}) == Failure(
        ("name",), "string", "Expected a string, but received: 1"
    )
    assert person.validate({"name": "john", "age": 42}) is None


@pytest.mark.id("tst_0t9xih")
def test_own_schema():
    """Keeps a schema of its own"""
    schema = {"name": String()}
    person = Object(schema)
    schema["age"] = Number()
    assert found(person, {"name": "john"}) == []
    assert Object({"id": String()}).schema != person.schema
