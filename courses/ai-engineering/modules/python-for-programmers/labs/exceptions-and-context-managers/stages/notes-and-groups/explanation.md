```python
def check_line(line, number, struct):
    record = parse_line(line, number)
    try:
        assert_(record, struct)
    except StructError as error:
        error.add_note(f"Line {number}")
        raise
    return record


def report(lines, struct, log):
    try:
        check_day(lines, struct)
    except* StructError as group:
        log.extend(f"{error.__notes__[-1]}: {error}" for error in group.exceptions)
```

A note adds to an error without changing it: the caller still gets the `StructError` that `assert_` raised, with its path, its failures and its traceback, and the line it came from. A new error raised in its place would lose them, unless it kept the old one as its cause, as `parse_line` does. Raised while another error is handled, an error keeps that one as its context even without `from`, and a traceback says it happened during the handling. `from error` says the new error is a direct result of it.

`except*` splits the group that `check_day` raises: the StructErrors come to the clause, and the rest go on in a group with the same message. A line that isn't JSON is the export's fault, not the record's, so `report` leaves it to its caller.
