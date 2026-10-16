def with_defaults(record, defaults):
    """A new dict: record's fields, then each field of defaults that record leaves out,
    made by calling its default when the default can be called."""
    raise NotImplementedError


def known_fields(record, fields):
    """A new dict of record's fields that are in fields, in record's order."""
    raise NotImplementedError


def unknown_fields(record, fields):
    """The names of record's fields that aren't in fields, in record's order."""
    raise NotImplementedError
