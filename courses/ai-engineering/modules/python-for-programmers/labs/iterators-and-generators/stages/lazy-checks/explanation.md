```python
def first_failure(value, schema):
    return next(failures(value, schema), None)


def check_records(records, schema):
    for index, record in enumerate(records):
        for path, message in failures(record, schema):
            yield index, path, message


def first_failures(records, schema, limit):
    return list(itertools.islice(check_records(records, schema), limit))
```

The generators chain. `islice` asks `check_records` for one failure at a time, `check_records` asks `failures` for one, and `failures` checks a value only when it's asked. `check_records` takes the next record only when the walk of the one before has nothing left. So `first_failures` reads the records up to its last failure's, and stops.

Anything a `for` loop can go through is an iterable, and `iter` gives an iterator for it, which `next` takes values from. A list gives a new iterator each time, starting from its first item, so it can be read again. A generator is its own iterator: once read, it's empty, and code that reads it a second time finds nothing.
