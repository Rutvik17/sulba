```python
def report(lines, schema, limit):
    records = (json.loads(line) for line in lines)
    return [
        (index + 1, path, message)
        for index, path, message in first_failures(records, schema, limit)
    ]
```

The generator expression reads a line and turns it into a record only when `first_failures` asks for the next record, so a whole day goes through one record at a time. The list comprehension is fine where it is: it holds only the failures, at most `limit` of them.

A file opened with `open` is an iterator of its lines too: it reads the file in chunks of a fixed size as its lines are asked for, so `report(open(path), ...)` never holds a whole export. Square brackets in the generator's place would read the whole day before checking any of it, and hold every record at once.
