```python
def with_defaults(record, defaults):
    result = dict(record)
    for key, default in defaults.items():
        if key not in result:
            result[key] = default() if callable(default) else default
    return result


def unknown_fields(record, fields):
    return [key for key in record if key not in fields]
```

`result = record` would give the same dict a second name, and the defaults would land in the caller's record. `dict(record)` is a new dict whose values are the same objects as the record's, so a list in it is still shared with the record.

JavaScript makes a default parameter afresh on each call. Python makes it once, when `def` runs, so `def f(tags=[])` gives every call that leaves `tags` out the same list. A factory such as `list` gives each record its own, as `field(default_factory=list)` does in a dataclass.

`if not result.get(key)` would replace `0`, `""` and `False` along with missing fields, since all three are falsy. Python's falsy values include empty lists and dicts too, which JavaScript treats as true, so a test of truth is no test of whether a field was sent.

A dict keeps its keys in the order they were added, so the unknown fields come out in the record's order. A set's order can change from one run to the next: Python seeds the hashes of strings with a random value in each process, so `set(record) - set(fields)` could list them differently each time.
