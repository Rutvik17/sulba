When a struct fails, superstruct reports the first failure and keeps the generator, so the rest are found only if they're asked for. The service works the same way: often it needs only to know whether a record passes, and a day's records arrive one at a time, more than it should hold at once.

`next(generator, default)` asks a generator for its next value, and gives `default` when there is none left. `itertools.islice(iterator, n)` gives an iterator's first `n` values, and asks it for no more: import `itertools` at the top of `walk.py` to use it. Write:

```
first_failure(value, schema) -> the first failure of value against schema, or None,
    checking nothing after it
check_records(records, schema) -> each failure of each record, as (index, path, message),
    reading a record only when the failures before it have been used
first_failures(records, schema, limit) -> the first limit failures of check_records,
    as a list, reading no record past them
```

`records` can be any iterable, such as a list or a generator that reads records from a file as they come. A generator gives each value once, so read it only once.
