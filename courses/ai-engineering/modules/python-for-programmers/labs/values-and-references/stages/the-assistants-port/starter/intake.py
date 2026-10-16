"""The intake service's checks, ported from superstruct."""

import math


def number(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return f"Expected a number, but received: {value!r}"
    if isinstance(value, float) and math.isnan(value):
        return f"Expected a number, but received: {value!r}"
    return None


def literal(value, constant):
    if value is constant:
        return None
    return f"Expected the literal `{constant!r}`, but received: {value!r}"


def enums(value, options):
    if value in options:
        return None
    shown = ",".join(repr(option) for option in options)
    return f"Expected one of `{shown}`, but received: {value!r}"


def with_defaults(record, defaults):
    result = record
    for key, default in defaults.items():
        if not result.get(key):
            result[key] = default() if callable(default) else default
    return result


def known_fields(record, fields):
    return {key: value for key, value in record.items() if key in fields}
