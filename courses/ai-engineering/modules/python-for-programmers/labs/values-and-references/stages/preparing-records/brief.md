The service is ready to take records from the form. Before it scores a sample, it prepares the record: it keeps the fields it knows, fills in the ones the form left out and checks each one, as superstruct's `mask` does with an object that has defaults, and it reports the fields it doesn't know. Write:

```
prepare(record, form, defaults) -> the prepared record, and its failures
```

`form` gives each field the service knows its check, such as `number`. `defaults` gives a default, or a factory for one, for each field the form may leave out.

The prepared record holds the form's fields, in the form's order, each from the record or else from its default. A field with neither is left out. The failures are pairs of a field and its message: first the form's fields that fail their checks, in the form's order, with `Missing` for a field left out that has no default; then the fields the form doesn't know, in the record's order, with `Unknown field`. Those aren't kept.

The service keeps prepared records for as long as it needs them, and changes them as it goes, so nothing it keeps may be shared. Python's `copy.deepcopy` copies a value and everything inside it: import `copy` at the top of `values.py` to use it. Hidden tests check what `prepare` gives, and three checks test it before it ships.
