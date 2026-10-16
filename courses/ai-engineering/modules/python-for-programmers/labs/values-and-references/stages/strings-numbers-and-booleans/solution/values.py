"""superstruct's checks, ported from JavaScript. Each takes a value and returns None when
the value passes, or a message saying why it doesn't."""

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
