"""The intake service's structs: enums, unions joined with a bar, and the clinic's own
messages."""

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class Failure:
    """One failure of a value against a struct."""

    path: tuple
    type: str
    message: str


class Missing:
    """The value of a field a record leaves out, shown as JavaScript shows undefined."""

    def __repr__(self):
        return "undefined"


MISSING = Missing()


class Struct:
    """A kind of value. A struct given a message fails a value of another kind with it, in
    place of superstruct's."""

    type = "unknown"

    def __init__(self, message=None):
        self.message = message

    def test(self, value):
        return None

    def entries(self, value):
        return ()

    def failures(self, value, path=()):
        found = self.test(value)
        if found is not None:
            yield Failure(path, self.type, self.message or found)
            return
        for key, item, struct in self.entries(value):
            yield from struct.failures(item, (*path, key))

    def validate(self, value):
        return next(self.failures(value), None)

    def __or__(self, other):
        if not isinstance(other, Struct):
            return NotImplemented
        if isinstance(self, Union):
            return Union([*self.members, other])
        return Union([self, other])

    def __contains__(self, value):
        return self.validate(value) is None


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


class Enums(Struct):
    """One of a list of options, as superstruct's enums is."""

    type = "enums"

    def __init__(self, options, message=None):
        super().__init__(message)
        self.options = list(options)

    def test(self, value):
        if value in self.options:
            return None
        shown = ",".join(repr(option) for option in self.options)
        return f"Expected one of `{shown}`, but received: {value!r}"


class Object(Struct):
    type = "object"

    def __init__(self, schema, message=None):
        super().__init__(message)
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


class Union(Struct):
    type = "union"

    def __init__(self, members, message=None):
        super().__init__(message)
        self.members = list(members)

    def failures(self, value, path=()):
        found = [list(member.failures(value, path)) for member in self.members]
        if not all(found):
            return
        shown = " | ".join(member.type for member in self.members)
        message = f"Expected the value to satisfy a union of `{shown}`, but received: {value!r}"
        yield Failure(path, self.type, self.message or message)
        for failures in found:
            yield from failures
