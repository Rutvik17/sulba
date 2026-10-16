"""superstruct's factories and refinements, ported from JavaScript. A check takes a value
and returns None when the value passes, or a message saying why it doesn't. Its __name__ is
its type in superstruct's messages."""

import functools
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

    def check(value):
        if same(value, constant):
            return None
        return f"Expected the literal `{constant!r}`, but received: {value!r}"

    return check


def enums(options):
    """A check that passes only the options, as they were when it was made."""
    options = tuple(options)
    shown = ",".join(repr(option) for option in options)

    def check(value):
        if any(same(value, option) for option in options):
            return None
        return f"Expected one of `{shown}`, but received: {value!r}"

    return check


def nullable(check):
    """A check that passes None as well as what check passes."""

    def nullable_check(value):
        if value is None:
            return None
        return check(value)

    return nullable_check


def size(check, low, high=None):
    """A check that passes what check passes when its size is from low to high, or is
    low when there is no high."""
    if high is None:
        high = low
    of = f"of `{low}`" if low == high else f"between `{low}` and `{high}`"

    def sized(value):
        message = check(value)
        if message is not None:
            return message
        if isinstance(value, (int, float)):
            if low <= value <= high:
                return None
            return f"Expected a {check.__name__} {of} but received `{value!r}`"
        length = len(value)
        if low <= length <= high:
            return None
        return (
            f"Expected a {check.__name__} with a length {of} "
            f"but received one with a length of `{length}`"
        )

    return sized


def refine(check, name, test):
    """A check that passes what check passes when test(value) is True. test can give a
    message of its own in place of False."""

    def refined(value):
        message = check(value)
        if message is not None:
            return message
        result = test(value)
        if result is True:
            return None
        if isinstance(result, str):
            return result
        return (
            f"Expected a value of type `{check.__name__}` with refinement `{name}`, "
            f"but received: `{value!r}`"
        )

    refined.__name__ = check.__name__
    return refined


def min_(check, threshold, exclusive=False):
    """A check that passes what check passes when it's at least threshold, or more than
    threshold when exclusive."""
    than = "" if exclusive else "or equal to "

    def test(value):
        if value > threshold or (value == threshold and not exclusive):
            return True
        return (
            f"Expected a {check.__name__} greater than {than}{threshold} "
            f"but received `{value!r}`"
        )

    return refine(check, "min", test)


def max_(check, threshold, exclusive=False):
    """A check that passes what check passes when it's at most threshold, or less than
    threshold when exclusive."""
    than = "" if exclusive else "or equal to "

    def test(value):
        if value < threshold or (value == threshold and not exclusive):
            return True
        return (
            f"Expected a {check.__name__} less than {than}{threshold} "
            f"but received `{value!r}`"
        )

    return refine(check, "max", test)


def pattern(check, regex):
    """A check that passes what check passes when regex matches somewhere in it."""

    def test(value):
        if regex.search(value):
            return True
        return (
            f"Expected a {check.__name__} matching `/{regex.pattern}/` "
            f"but received {value!r}"
        )

    return refine(check, "pattern", test)


def define(name):
    """A decorator that makes a check of type name from a test, as superstruct's define
    makes a struct."""

    def decorate(test):
        @functools.wraps(test)
        def check(value):
            result = test(value)
            if result is True:
                return None
            if isinstance(result, str):
                return result
            return f"Expected a value of type `{name}`, but received: `{value!r}`"

        check.__name__ = name
        return check

    return decorate


def counted(check):
    """check, counting in its failed attribute the values it has failed."""

    @functools.wraps(check)
    def counting(value):
        message = check(value)
        if message is not None:
            counting.failed += 1
        return message

    counting.failed = 0
    return counting
