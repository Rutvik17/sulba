def same(a, b):
    """Whether JavaScript's a === b would be true, for values JSON gives."""
    raise NotImplementedError


def literal(value, constant):
    """None when value === constant, as superstruct's literal checks."""
    raise NotImplementedError


def enums(value, options):
    """None when options.includes(value), as superstruct's enums checks."""
    raise NotImplementedError
