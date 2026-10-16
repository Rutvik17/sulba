```python
def prepare(record, form, defaults):
    prepared = {}
    failures = []
    for field, check in form.items():
        if field in record:
            value = copy.deepcopy(record[field])
        elif field in defaults:
            default = defaults[field]
            value = default() if callable(default) else copy.deepcopy(default)
        else:
            failures.append((field, "Missing"))
            continue
        prepared[field] = value
        message = check(value)
        if message is not None:
            failures.append((field, message))
    failures.extend((field, "Unknown field") for field in unknown_fields(record, form))
    return prepared, failures
```

Going through `form` gives the prepared record the form's order, whatever order the record arrives in, and `unknown_fields` keeps the record's order for the rest.

`copy.deepcopy` copies a list and the lists and dicts inside it, where `dict(record)` stops at the first level. A number, a string, `True` or `None` can't be changed in place, so sharing one is harmless. A default given as a value is copied for each record as well, since a list given as a default would otherwise be shared by every record that left the field out.

A pair such as `(field, message)` is a tuple, a sequence that can't be changed once made: it suits a pair whose parts belong together, where a list suits items that come and go.
