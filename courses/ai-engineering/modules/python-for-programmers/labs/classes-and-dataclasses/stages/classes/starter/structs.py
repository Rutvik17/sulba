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
        raise NotImplementedError

    def validate(self, value):
        """The first Failure of value, or None."""
        raise NotImplementedError


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


class Object(Struct):
    """An object with a struct for each of its fields, as superstruct's object is."""


class Array(Struct):
    """An array whose items each match one struct, as superstruct's array is."""


class Type(Object):
    """An object that may hold fields its schema doesn't know, as superstruct's type is."""
