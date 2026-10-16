"""superstruct's checks of whole records, ported from JavaScript. A schema is a check of
one value, a dict of schemas for an object's fields, a list holding the schema of an
array's items, or a tuple of the schemas of a fixed-length array's items."""

import itertools
import json
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


def never(value):
    """superstruct's message for a value the schema has no place for."""
    return f"Expected a value of type `never`, but received: `{value!r}`"


def failures(value, schema, path=()):
    """Each failure of value against schema, as a (path, message) pair, in superstruct's
    order."""
    if isinstance(schema, dict):
        if not isinstance(value, dict):
            yield path, f"Expected an object, but received: {value!r}"
            return
        for key, field in schema.items():
            if key in value:
                yield from failures(value[key], field, (*path, key))
            else:
                yield (*path, key), "Missing"
        for key in value:
            if key not in schema:
                yield (*path, key), never(value[key])
    elif isinstance(schema, list):
        if not isinstance(value, list):
            yield path, f"Expected an array value, but received: {value!r}"
            return
        for index, item in enumerate(value):
            yield from failures(item, schema[0], (*path, index))
    elif isinstance(schema, tuple):
        if not isinstance(value, list):
            yield path, f"Expected an array, but received: {value!r}"
            return
        for index in range(max(len(schema), len(value))):
            if index >= len(value):
                yield (*path, index), "Missing"
            elif index >= len(schema):
                yield (*path, index), never(value[index])
            else:
                yield from failures(value[index], schema[index], (*path, index))
    else:
        message = schema(value)
        if message is not None:
            yield path, message


def first_failure(value, schema):
    """The first failure of value against schema, or None, checking nothing after it."""
    return next(failures(value, schema), None)


def check_records(records, schema):
    """Each failure of each record, as (index, path, message), reading a record only when
    the failures before it have been used."""
    for index, record in enumerate(records):
        for path, message in failures(record, schema):
            yield index, path, message


def first_failures(records, schema, limit):
    """The first limit failures of check_records, as a list, reading no record past
    them."""
    return list(itertools.islice(check_records(records, schema), limit))


def report(lines, schema, limit):
    """The first limit failures of a day's records, one JSON object a line, as
    (line number, path, message), reading no line past them."""
    records = (json.loads(line) for line in lines)
    return [
        (index + 1, path, message)
        for index, path, message in first_failures(records, schema, limit)
    ]
