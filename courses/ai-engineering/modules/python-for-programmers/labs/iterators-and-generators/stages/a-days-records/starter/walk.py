def report(lines, schema, limit):
    """The first limit failures of a day's records, one JSON object a line, as
    (line number, path, message), reading no line past them."""
    raise NotImplementedError
