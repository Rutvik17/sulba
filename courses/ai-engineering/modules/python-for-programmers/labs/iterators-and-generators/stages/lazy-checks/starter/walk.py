def first_failure(value, schema):
    """The first failure of value against schema, or None, checking nothing after it."""
    raise NotImplementedError


def check_records(records, schema):
    """Each failure of each record, as (index, path, message), reading a record only when
    the failures before it have been used."""
    raise NotImplementedError


def first_failures(records, schema, limit):
    """The first limit failures of check_records, as a list, reading no record past
    them."""
    raise NotImplementedError
