def never(value):
    """superstruct's message for a value the schema has no place for."""
    return f"Expected a value of type `never`, but received: `{value!r}`"


def failures(value, schema, path=()):
    """Each failure of value against schema, as a (path, message) pair, in superstruct's
    order."""
    raise NotImplementedError
