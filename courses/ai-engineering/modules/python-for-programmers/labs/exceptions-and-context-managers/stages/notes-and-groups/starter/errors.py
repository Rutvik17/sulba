def parse_line(line, number):
    """The record on line number of a day's export, or raises a ValueError that names the
    line, from json's own error."""
    raise NotImplementedError


def check_line(line, number, struct):
    """The record on line number when it passes struct, or raises its StructError, with a
    note that names the line."""
    raise NotImplementedError


def check_day(lines, struct):
    """The records of a day's lines, numbered from 1, or raises an ExceptionGroup of every
    line's error, in order."""
    raise NotImplementedError


def report(lines, struct, log):
    """Adds "Line n: message" to log for each line whose record fails struct. Every other
    error of the day reaches the caller, in a group."""
    raise NotImplementedError
