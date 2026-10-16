"""superstruct's factories and refinements, ported from JavaScript. A check takes a value
and returns None when the value passes, or a message saying why it doesn't. Its __name__ is
its type in superstruct's messages."""

import math


def string(value):
    """None for a str."""
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


def same(a, b):
    """Whether JavaScript's a === b would be true, for values JSON gives."""
    if isinstance(a, (list, dict)) or isinstance(b, (list, dict)):
        return a is b
    if isinstance(a, bool) or isinstance(b, bool):
        return isinstance(a, bool) and isinstance(b, bool) and a == b
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return a == b
    return type(a) is type(b) and a == b


def literal(constant):
    """A check that passes only constant."""
    raise NotImplementedError


def enums(options):
    """A check that passes only the options, as they were when it was made."""
    raise NotImplementedError


def nullable(check):
    """A check that passes None as well as what check passes."""
    raise NotImplementedError


def size(check, low, high=None):
    """A check that passes what check passes when its size is from low to high, or is
    low when there is no high."""
    raise NotImplementedError
