def define(name):
    """A decorator that makes a check of type name from a test, as superstruct's define
    makes a struct."""
    raise NotImplementedError


def counted(check):
    """check, counting in its failed attribute the values it has failed."""
    raise NotImplementedError
