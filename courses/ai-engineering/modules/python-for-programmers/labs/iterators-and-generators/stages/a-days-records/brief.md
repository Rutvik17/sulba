At the end of each day, the form's server exports the day's records as JSON Lines: a file with one record on each line, written as a JSON object. The service checks each export as it comes in. Write:

```
report(lines, schema, limit) -> the first limit failures of the day's records, as
    (line number, path, message), reading no line past them
```

`lines` is any iterable of lines, such as an open file, which gives its lines one at a time. Number them from `1`, as an editor does. `json.loads` reads one line, and ignores the `\n` or `\r\n` at its end: import `json` at the top of `walk.py` to use it.

An export can hold more records than the service has memory for, so hold one at a time. Hidden tests check what `report` gives, and two checks test it before it ships.
