class StructError(TypeError):
    """A value that fails a struct, with superstruct's message."""


class Struct:
    """A check of values of one type: its name, and a test that tells values of the type
    apart."""

    def __init__(self, name, test):
        self.name = name
        self.test = test


def string():
    """A struct of strings."""
    raise NotImplementedError


def number():
    """A struct of numbers."""
    raise NotImplementedError


def array(item):
    """A struct of lists whose every item passes item."""
    raise NotImplementedError


def nullable(struct):
    """The struct, with None let through."""
    raise NotImplementedError


def is_(value, struct):
    """Whether the value passes the struct."""
    raise NotImplementedError


def create(value, struct):
    """The value, as the struct's type, or StructError when it fails the struct."""
    raise NotImplementedError
