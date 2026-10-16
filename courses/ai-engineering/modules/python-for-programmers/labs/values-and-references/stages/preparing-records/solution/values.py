"""superstruct's checks, ported from JavaScript. Each takes a value and returns None when
the value passes, or a message saying why it doesn't."""

import copy
import math


def string(value):
    """None for a str, as JavaScript's typeof says string."""
    if isinstance(value, str):
        return None
    return f"Expected a string, but received: {value!r}"


def is_number(value):
    """Whether JavaScript's typeof would call value a number, and it isn't NaN."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    return isinstance(value, int) or not math.isnan(value)


def number(value):
    """None for what JavaScript's typeof calls a number, other than NaN."""
    if is_number(value):
        return None
    return f"Expected a number, but received: {value!r}"


def integer(value):
    """None for a number with no fraction, as JavaScript's Number.isInteger says."""
    if is_number(value) and (isinstance(value, int) or value.is_integer()):
        return None
    return f"Expected an integer, but received: {value!r}"


def boolean(value):
    """None for True or False."""
    if isinstance(value, bool):
        return None
    return f"Expected a value of type `boolean`, but received: `{value!r}`"


def same(a, b):
    """Whether JavaScript's a === b would be true, for values JSON gives."""
    if isinstance(a, (list, dict)) or isinstance(b, (list, dict)):
        return a is b
    if isinstance(a, bool) or isinstance(b, bool):
        return isinstance(a, bool) and isinstance(b, bool) and a == b
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return a == b
    return type(a) is type(b) and a == b


def is_nan(value):
    return isinstance(value, float) and math.isnan(value)


def literal(value, constant):
    """None when value === constant, as superstruct's literal checks."""
    if same(value, constant):
        return None
    return f"Expected the literal `{constant!r}`, but received: {value!r}"


def enums(value, options):
    """None when options.includes(value), as superstruct's enums checks."""
    for option in options:
        if same(value, option) or (is_nan(value) and is_nan(option)):
            return None
    shown = ",".join(repr(option) for option in options)
    return f"Expected one of `{shown}`, but received: {value!r}"


def with_defaults(record, defaults):
    """A new dict: record's fields, then each field of defaults that record leaves out,
    made by calling its default when the default can be called."""
    result = dict(record)
    for key, default in defaults.items():
        if key not in result:
            result[key] = default() if callable(default) else default
    return result


def known_fields(record, fields):
    """A new dict of record's fields that are in fields, in record's order."""
    return {key: value for key, value in record.items() if key in fields}


def unknown_fields(record, fields):
    """The names of record's fields that aren't in fields, in record's order."""
    return [key for key in record if key not in fields]


def prepare(record, form, defaults):
    """The record as the service keeps it, and its failures, as (field, message) pairs."""
    prepared = {}
    failures = []
    for field, check in form.items():
        if field in record:
            value = copy.deepcopy(record[field])
        elif field in defaults:
            default = defaults[field]
            value = default() if callable(default) else copy.deepcopy(default)
        else:
            failures.append((field, "Missing"))
            continue
        prepared[field] = value
        message = check(value)
        if message is not None:
            failures.append((field, message))
    failures.extend((field, "Unknown field") for field in unknown_fields(record, form))
    return prepared, failures
