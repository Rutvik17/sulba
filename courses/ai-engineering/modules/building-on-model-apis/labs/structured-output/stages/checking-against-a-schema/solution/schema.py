"""Checks a JSON value against a JSON Schema: the keywords the shop's assistant uses, as JSON
Schema 2020-12 defines them."""

import re
from dataclasses import dataclass
from typing import Any

# A key that a JSON path can name after a dot; any other goes in brackets.
NAME = re.compile(r"[a-zA-Z][a-zA-Z0-9_]*")


@dataclass(frozen=True)
class Error:
    """Where a value fails its schema: its JSON path, such as `$.bikes`, the keyword it fails,
    and what's wrong, for a person or a model to read."""

    path: str
    keyword: str
    message: str


def errors(value: Any, schema: dict[str, Any], path: str = "$") -> list[Error]:
    """Every way value fails schema, value being at path in the reply."""
    found = []

    def fail(keyword: str, message: str) -> None:
        found.append(Error(path, keyword, message))

    if "type" in schema:
        types = schema["type"] if isinstance(schema["type"], list) else [schema["type"]]
        if not any(is_type(value, kind) for kind in types):
            fail("type", f"{value!r} is not of type {' or '.join(types)}")
    if "enum" in schema and not any(equal(value, each) for each in schema["enum"]):
        fail("enum", f"{value!r} is not one of {schema['enum']!r}")
    if "const" in schema and not equal(value, schema["const"]):
        fail("const", f"{schema['const']!r} was expected")
    if is_type(value, "object"):
        properties = schema.get("properties", {})
        for key, subschema in properties.items():
            if key in value:
                found += errors(value[key], subschema, child(path, key))
        for key in schema.get("required", []):
            if key not in value:
                fail("required", f"{key!r} is a required property")
        extra = [key for key in value if key not in properties]
        additional = schema.get("additionalProperties", True)
        if isinstance(additional, dict):
            for key in extra:
                found += errors(value[key], additional, child(path, key))
        elif additional is False and extra:
            fail("additionalProperties", f"{', '.join(map(repr, extra))} not allowed")
    if is_type(value, "array"):
        if "items" in schema:
            for index, item in enumerate(value):
                found += errors(item, schema["items"], f"{path}[{index}]")
        if len(value) < schema.get("minItems", 0):
            fail("minItems", f"has fewer than {schema['minItems']} items")
        if "maxItems" in schema and len(value) > schema["maxItems"]:
            fail("maxItems", f"has more than {schema['maxItems']} items")
    if is_type(value, "number"):
        if "minimum" in schema and value < schema["minimum"]:
            fail("minimum", f"{value!r} is less than {schema['minimum']!r}")
        if "maximum" in schema and value > schema["maximum"]:
            fail("maximum", f"{value!r} is more than {schema['maximum']!r}")
    if is_type(value, "string"):
        if len(value) < schema.get("minLength", 0):
            fail("minLength", f"{value!r} is shorter than {schema['minLength']}")
        if "maxLength" in schema and len(value) > schema["maxLength"]:
            fail("maxLength", f"{value!r} is longer than {schema['maxLength']}")
        if "pattern" in schema and not re.search(schema["pattern"], value):
            fail("pattern", f"{value!r} does not match {schema['pattern']!r}")
    return found


def is_type(value: Any, kind: str) -> bool:
    """Whether value has the JSON type kind. A bool is no number, and an integer is any number
    with no fractional part."""
    match kind:
        case "null":
            return value is None
        case "boolean":
            return isinstance(value, bool)
        case "integer":
            if isinstance(value, float):
                return value.is_integer()
            return isinstance(value, int) and not isinstance(value, bool)
        case "number":
            return isinstance(value, int | float) and not isinstance(value, bool)
        case "string":
            return isinstance(value, str)
        case "array":
            return isinstance(value, list)
        case "object":
            return isinstance(value, dict)
    raise ValueError(f"Unknown type {kind!r}")


def equal(one: Any, other: Any) -> bool:
    """Whether two JSON values are equal: of the same type with the same value, numbers by
    their value, so 1 equals 1.0 but not true."""
    if isinstance(one, bool) or isinstance(other, bool):
        return isinstance(one, bool) and isinstance(other, bool) and one == other
    if isinstance(one, list) and isinstance(other, list):
        return len(one) == len(other) and all(map(equal, one, other))
    if isinstance(one, dict) and isinstance(other, dict):
        return one.keys() == other.keys() and all(equal(one[k], other[k]) for k in one)
    if is_type(one, "number") and is_type(other, "number"):
        return bool(one == other)
    return type(one) is type(other) and one == other


def child(path: str, key: str) -> str:
    """The JSON path of an object's key, after a dot when it's a name, in brackets otherwise."""
    if NAME.fullmatch(key):
        return f"{path}.{key}"
    escaped = key.replace("\\", "\\\\").replace("'", "\\'")
    return f"{path}['{escaped}']"
