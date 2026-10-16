"""superstruct's errors, ported: the error a value that fails raises, and the ways to check
a value with it."""

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class Failure:
    """One failure of a value against a struct: the value, the path to it, the type of the
    struct it failed, superstruct's message, and the refinement it failed, if any."""

    value: object
    path: tuple
    type: str
    message: str
    refinement: str | None = None


class Missing:
    """The value of a field a record leaves out, shown as JavaScript shows undefined."""

    def __repr__(self):
        return "undefined"


MISSING = Missing()


class Struct:
    """A kind of value: its type, a test of a value, and the values inside one that passes."""

    type = "unknown"

    def test(self, value):
        """None when value is of this struct's kind, or superstruct's message."""
        return None

    def entries(self, value):
        """Each value inside value, as (key, value, struct)."""
        return ()

    def failures(self, value, path=()):
        """Each Failure of value against this struct, found as it's asked for."""
        message = self.test(value)
        if message is not None:
            yield Failure(value, path, self.type, message)
            return
        for key, item, struct in self.entries(value):
            yield from struct.failures(item, (*path, key))


class String(Struct):
    type = "string"

    def test(self, value):
        if isinstance(value, str):
            return None
        return f"Expected a string, but received: {value!r}"


class Number(Struct):
    type = "number"

    def test(self, value):
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return f"Expected a number, but received: {value!r}"
        if isinstance(value, float) and math.isnan(value):
            return f"Expected a number, but received: {value!r}"
        return None


class Never(Struct):
    type = "never"

    def test(self, value):
        return f"Expected a value of type `never`, but received: `{value!r}`"


class Object(Struct):
    type = "object"

    def __init__(self, schema):
        self.schema = dict(schema)

    def test(self, value):
        if isinstance(value, dict):
            return None
        return f"Expected an object, but received: {value!r}"

    def entries(self, value):
        for key, struct in self.schema.items():
            yield key, value.get(key, MISSING), struct
        for key in value:
            if key not in self.schema:
                yield key, value[key], Never()


class StructError(TypeError):
    """superstruct's StructError: a TypeError for a value's first failure, which finds the
    rest when they're asked for."""

    def __init__(self, failure, rest):
        raise NotImplementedError

    def failures(self):
        """Every failure of the value, the first included, found the first time they're
        asked for."""
        raise NotImplementedError


def assert_(value, struct):
    """None when value passes struct, or raises the StructError of its first failure."""
    raise NotImplementedError


def validate(value, struct):
    """(None, value) when value passes struct, or (error, None) with its StructError."""
    raise NotImplementedError


def is_(value, struct):
    """Whether value passes struct."""
    raise NotImplementedError
