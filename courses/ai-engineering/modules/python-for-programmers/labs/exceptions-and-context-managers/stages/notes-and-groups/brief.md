At the end of each day, the form's server exports the day's records as JSON Lines, one record on each line, and the service checks the export line by line. A line can fail in two ways: its record can fail the struct, or the line can be no JSON at all. The service's log must say which line failed, and how. Write:

```
parse_line(line, number) -> the record on the line, or raises a ValueError that names
    the line, from json's own error
check_line(line, number, struct) -> the record when it passes struct, or raises its
    StructError, with a note that names the line
check_day(lines, struct) -> the day's records, or raises an ExceptionGroup of every
    line's error, in order
report(lines, struct, log) -> adds a line to log for each record that fails struct,
    and lets every other error of the day reach the caller, in a group
```

with these messages, and notes such as `Line 2`:

```
Line 3 isn't JSON
3 of 5 lines failed
Line 2: At path: radius -- Expected a number, but received: 'x'
```

`json.loads` reads a line: import `json` at the top of `errors.py` to use it. `raise ValueError(message) from error` gives the new error the one being handled as its cause, as `new Error(message, { cause: error })` does in JavaScript, and a traceback shows both. `error.add_note(note)` adds a line that a traceback shows after the error's message, and `error.__notes__` is the list of them. `raise` with nothing after it raises the error being handled again, as it was.

`raise ExceptionGroup(message, errors)` raises several errors together, as JavaScript's `AggregateError` does. `except* StructError as group:` handles the group's StructErrors, as a group of their own, and the group's other errors go on to the caller. `return` can't be used inside an `except*` clause.
