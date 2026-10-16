The form can leave a field out, such as a note on a sample. superstruct's `defaulted` fills in the fields a record leaves out, on a copy, so its changes never reach the data it was given:

```js
const ret = { ...x }
for (const key in f) {
  if (ret[key] === undefined) ret[key] = f[key]
}
```

`{ ...x }` is a shallow copy: a new object with the same fields, whose values are the same objects as before. In Python, a variable holds a reference to an object too, and `dict(record)`, `record.copy()` and `{**record}` each make a shallow copy.

A field the form leaves out is missing from the dict. That isn't the same as a field the form sends as `null`, which arrives as `None`, and superstruct fills only the first.

A default list must not be shared, or a tag added to one record's list would be added to every record's. Python's habit is a factory, a function that makes a new value each time it's called, as `list` does. Write:

```
with_defaults(record, defaults) -> a new dict: record's fields, then each field of
    defaults that record leaves out, made by calling its default when it can be called
known_fields(record, fields) -> a new dict of record's fields that are in fields,
    in record's order
unknown_fields(record, fields) -> the names of record's fields that aren't in fields,
    in record's order
```

None of them may change `record`.
