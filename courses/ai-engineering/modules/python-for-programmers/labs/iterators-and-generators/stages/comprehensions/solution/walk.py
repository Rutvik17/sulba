"""superstruct's checks of whole records, ported from JavaScript. A schema is a check of
one value, a dict of schemas for an object's fields, a list holding the schema of an
array's items, or a tuple of the schemas of a fixed-length array's items."""

import math


def string(value):
    """None for a str, or superstruct's message."""
    if isinstance(value, str):
        return None
    return f"Expected a string, but received: {value!r}"


def number(value):
    """None for what JavaScript's typeof calls a number, other than NaN."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return f"Expected a number, but received: {value!r}"
    if isinstance(value, float) and math.isnan(value):
        return f"Expected a number, but received: {value!r}"
    return None


def boolean(value):
    """None for True or False."""
    if isinstance(value, bool):
        return None
    return f"Expected a value of type `boolean`, but received: `{value!r}`"


def pick(schema, keys):
    """A schema of schema's fields named in keys, in the order of keys."""
    return {key: schema[key] for key in keys}


def omit(schema, keys):
    """A schema of the fields of schema not named in keys, in schema's order."""
    return {key: field for key, field in schema.items() if key not in keys}


def assign(*schemas):
    """One schema with the fields of all of schemas, a later schema's field winning."""
    return {key: field for schema in schemas for key, field in schema.items()}


def explain(path, message):
    """superstruct's message for a failure at path."""
    if not path:
        return message
    shown = ".".join(str(key) for key in path)
    return f"At path: {shown} -- {message}"
