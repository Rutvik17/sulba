"""superstruct's structs and their failures, ported from JavaScript to classes."""

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class Failure:
    """One failure of a value against a struct: the path to the value, the type of the
    struct it failed, superstruct's message, and the refinement it failed, if any."""

    path: tuple
    type: str
    message: str
    refinement: str | None = None

    @property
    def key(self):
        """The key or index of the value in the one around it, or None at the top."""
        return self.path[-1] if self.path else None

    def explain(self):
        """superstruct's message for the failure, with its path."""
        if not self.path:
            return self.message
        shown = ".".join(str(key) for key in self.path)
        return f"At path: {shown} -- {self.message}"


class Missing:
    """The value of a field a record leaves out, shown as JavaScript shows undefined."""

    def __repr__(self):
        return "undefined"


MISSING = Missing()


class Struct:
    """A kind of value, as superstruct's Struct is: its type, a test of a value, and the
    values inside a value that passes, each with a struct of its own."""

    type = "unknown"

    def test(self, value):
        """None when value is of this struct's kind, or superstruct's message."""
        return None

    def entries(self, value):
        """Each value inside value, as (key, value, struct). There are none here."""
        return ()

    def failures(self, value, path=()):
        """Each Failure of value against this struct and the structs inside it."""
        message = self.test(value)
        if message is not None:
            yield Failure(path, self.type, message)
            return
        for key, item, struct in self.entries(value):
            yield from struct.failures(item, (*path, key))

    def validate(self, value):
        """The first Failure of value, or None."""
        return next(self.failures(value), None)

    def __or__(self, other):
        if not isinstance(other, Struct):
            return NotImplemented
        left = self.members if isinstance(self, Union) else (self,)
        right = other.members if isinstance(other, Union) else (other,)
        return Union([*left, *right])

    def __contains__(self, value):
        return self.validate(value) is None

    def __repr__(self):
        return f"{type(self).__name__}()"


class String(Struct):
    type = "string"

    def test(self, value):
        if isinstance(value, str):
            return None
        return f"Expected a string, but received: {value!r}"


class Never(Struct):
    """The struct of a field the schema doesn't know: no value passes."""

    type = "never"

    def test(self, value):
        return f"Expected a value of type `never`, but received: `{value!r}`"


class Number(Struct):
    """What JavaScript's typeof calls a number, other than NaN."""

    type = "number"

    def test(self, value):
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return f"Expected a number, but received: {value!r}"
        if isinstance(value, float) and math.isnan(value):
            return f"Expected a number, but received: {value!r}"
        return None


class Object(Struct):
    """An object with a struct for each of its fields, as superstruct's object is."""

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

    def __getitem__(self, key):
        return self.schema[key]

    def __repr__(self):
        return f"{type(self).__name__}({self.schema!r})"


class Array(Struct):
    """An array whose items each match one struct, as superstruct's array is."""

    type = "array"

    def __init__(self, element):
        self.element = element

    def test(self, value):
        if isinstance(value, list):
            return None
        return f"Expected an array value, but received: {value!r}"

    def entries(self, value):
        for index, item in enumerate(value):
            yield index, item, self.element

    def __repr__(self):
        return f"{type(self).__name__}({self.element!r})"


class Type(Object):
    """An object that may hold fields its schema doesn't know, as superstruct's type is."""

    type = "type"

    def entries(self, value):
        for key, item, struct in super().entries(value):
            if key in self.schema:
                yield key, item, struct


class Union(Struct):
    """A value that passes any one of its members, as superstruct's union is."""

    type = "union"

    def __init__(self, members):
        self.members = tuple(members)

    def failures(self, value, path=()):
        found = [list(member.failures(value, path)) for member in self.members]
        if not all(found):
            return
        shown = " | ".join(member.type for member in self.members)
        message = f"Expected the value to satisfy a union of `{shown}`, but received: {value!r}"
        yield Failure(path, self.type, message)
        for failures in found:
            yield from failures

    def __repr__(self):
        return " | ".join(repr(member) for member in self.members)
