"""superstruct's checks, ported from JavaScript. Each takes a value and returns None when
the value passes, or a message saying why it doesn't."""

import math


def string(value):
    """None for a str, as JavaScript's typeof says string."""
    if isinstance(value, str):
        return None
    return f"Expected a string, but received: {value!r}"


def number(value):
    """None for what JavaScript's typeof calls a number, other than NaN."""
    raise NotImplementedError


def integer(value):
    """None for a number with no fraction, as JavaScript's Number.isInteger says."""
    raise NotImplementedError


def boolean(value):
    """None for True or False."""
    raise NotImplementedError
