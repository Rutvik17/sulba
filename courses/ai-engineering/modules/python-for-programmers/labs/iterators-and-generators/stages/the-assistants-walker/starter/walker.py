"""The service's checks of whole records, ported from superstruct."""

import itertools
import math


def string(value):
    if isinstance(value, str):
        return None
    return f"Expected a string, but received: {value!r}"


def number(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return f"Expected a number, but received: {value!r}"
    if isinstance(value, float) and math.isnan(value):
        return f"Expected a number, but received: {value!r}"
    return None


def never(value):
    return f"Expected a value of type `never`, but received: `{value!r}`"


def failures(value, schema, path=()):
    if isinstance(schema, dict):
        if not isinstance(value, dict):
            return path, f"Expected an object, but received: {value!r}"
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
            failures(item, schema[0], (*path, index))
    else:
        message = schema(value)
        if message is not None:
            yield path, message


def explain(path, message):
    if not path:
        return message
    shown = ".".join(str(key) for key in path)
    return f"At path: {shown} -- {message}"


def problems(value, schema, limit=None):
    """superstruct's messages for the first limit failures, or for all of them."""
    found = failures(value, schema)
    if not any(found):
        return []
    return [explain(path, message) for path, message in itertools.islice(found, limit)]


def first_failures(records, schema, limit):
    """The first limit failures of the records, as (index, path, message)."""
    found = [
        (index, path, message)
        for index, record in enumerate(records)
        for path, message in failures(record, schema)
    ]
    return found[:limit]
