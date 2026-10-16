import pytest

from walk import failures, number, string

PERSON = {"name": string, "age": number}


def found(value, schema):
    return list(failures(value, schema))


@pytest.mark.id("tst_8mhga9")
def test_objects():
    """Passes superstruct's tests for objects"""
    assert found({"name": "john", "age": 42}, PERSON) == []
    assert found("invalid", PERSON) == [
        ((), "Expected an object, but received: 'invalid'")
    ]
    assert found([], {}) == [((), "Expected an object, but received: []")]
    # test/validation/object/invalid-property.ts
    value = {"name": "john", "age": "invalid", "height": 2}
    assert found(value, {**PERSON, "height": string}) == [
        (("age",), "Expected a number, but received: 'invalid'"),
        (("height",), "Expected a string, but received: 2"),
    ]
    # test/validation/object/invalid-property-unknown.ts
    assert found({"name": "john", "age": 42, "unknown": True}, PERSON) == [
        (("unknown",), "Expected a value of type `never`, but received: `True`")
    ]


@pytest.mark.id("tst_225ltz")
def test_nested():
    """Passes superstruct's tests for nested objects and arrays"""
    # test/validation/object/invalid-property-nested.ts
    schema = {"name": string, "address": {"street": string, "city": string}}
    value = {"name": "john", "address": {"street": 123, "city": "Springfield"}}
    assert found(value, schema) == [
        (("address", "street"), "Expected a string, but received: 123")
    ]
    # test/validation/object/invalid-element-nested.ts
    schema = {"name": string, "emails": [string]}
    value = {"name": "john", "emails": ["name@example.com", False]}
    assert found(value, schema) == [
        (("emails", 1), "Expected a string, but received: False")
    ]
    # test/validation/array/invalid-element-property.ts
    value = [{"id": "1"}, {"id": False}, {"id": "3"}]
    assert found(value, [{"id": string}]) == [
        ((1, "id"), "Expected a string, but received: False")
    ]


@pytest.mark.id("tst_csvqy6")
def test_arrays():
    """Passes superstruct's tests for arrays"""
    assert found([1, 2, 3], [number]) == []
    assert found([], [number]) == []
    assert found([1, "invalid", 3], [number]) == [
        ((1,), "Expected a number, but received: 'invalid'")
    ]
    assert found("invalid", [number]) == [
        ((), "Expected an array value, but received: 'invalid'")
    ]


@pytest.mark.id("tst_296u11")
def test_tuples():
    """Passes superstruct's tests for tuples"""
    pair = (string, number)
    assert found(["A", 1], pair) == []
    assert found([False, 3], pair) == [((0,), "Expected a string, but received: False")]
    assert found(["A"], pair) == [((1,), "Missing")]
    assert found(["A", 3, "unknown"], pair) == [
        ((2,), "Expected a value of type `never`, but received: `'unknown'`")
    ]
    assert found("invalid", pair) == [
        ((), "Expected an array, but received: 'invalid'")
    ]


@pytest.mark.id("tst_ojg859")
def test_missing():
    """Reports the fields a value leaves out"""
    schema = {"id": string, "address": {"street": string}}
    assert found({}, schema) == [(("id",), "Missing"), (("address",), "Missing")]
    assert found({"id": "842302", "address": {}}, schema) == [
        (("address", "street"), "Missing")
    ]


@pytest.mark.id("tst_oz2zca")
def test_order():
    """Gives the schema's fields first, then the unknown ones in the value's order"""
    schema = {"b": number, "a": number}
    unknown = list("qwertyuiopsdfghjklzxcvnm")
    value = {"a": "x", **dict.fromkeys(unknown, 1), "b": "x"}
    paths = [path for path, _ in found(value, schema)]
    assert paths == [("b",), ("a",), *((key,) for key in unknown)]


@pytest.mark.id("tst_yh83nh")
def test_lazy():
    """Checks each value only when asked for the next failure"""
    checked = []

    def logged(value):
        checked.append(value)
        return number(value)

    walking = failures(
        {"a": "x", "b": 2, "c": "y"}, {"a": logged, "b": logged, "c": logged}
    )
    assert checked == []
    assert next(walking) == (("a",), "Expected a number, but received: 'x'")
    assert checked == ["x"]
    assert next(walking) == (("c",), "Expected a number, but received: 'y'")
    assert checked == ["x", 2, "y"]


@pytest.mark.id("tst_2khyg7")
def test_paths_are_tuples():
    """Gives each path as a tuple"""
    paths = [path for path, _ in found({"a": ["x", "y", "z"]}, {"a": [number]})]
    assert paths == [("a", 0), ("a", 1), ("a", 2)]
    assert all(isinstance(path, tuple) for path in paths)
