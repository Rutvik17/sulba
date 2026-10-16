"""The intake form's checks, built from its spec."""

import math


def counted(check):
    def counting(value):
        message = check(value)
        if message is not None:
            counting.failed += 1
        return message

    counting.failed = 0
    return counting


def number(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return f"Expected a number, but received: {value!r}"
    if isinstance(value, float) and math.isnan(value):
        return f"Expected a number, but received: {value!r}"
    return None


def enums(options):
    shown = ",".join(repr(option) for option in options)

    def check(value):
        if value in options:
            return None
        return f"Expected one of `{shown}`, but received: {value!r}"

    return check


def refine(check, name, test):
    def refined(value):
        result = test(value)
        message = check(value)
        if message is not None:
            return message
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


def build(spec):
    """A counted check for each measurement in spec, given as (field, low, high)."""
    checks = {}
    for field, low, high in spec:
        checks[field] = counted(
            refine(number, "range", lambda value: low <= value <= high)
        )
    return checks
