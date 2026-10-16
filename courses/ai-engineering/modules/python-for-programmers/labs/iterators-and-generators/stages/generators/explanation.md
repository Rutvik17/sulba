```python
def failures(value, schema, path=()):
    if isinstance(schema, dict):
        if not isinstance(value, dict):
            yield path, f"Expected an object, but received: {value!r}"
            return
        for key, field in schema.items():
            if key in value:
                yield from failures(value[key], field, (*path, key))
            else:
                yield (*path, key), "Missing"
        for key in value:
            if key not in schema:
                yield (*path, key), never(value[key])
    ...
    else:
        message = schema(value)
        if message is not None:
            yield path, message
```

Calling `failures` runs none of it. The generator it returns runs the body as far as the first `yield` when it's asked for a value, and stays there until it's asked for the next. So a walk of a large record does no more work than the failures that are read from it need.

`yield from` passes on everything the walk of a field yields, as superstruct's inner `for` loop does. Each level makes its path a new tuple, `(*path, key)`, and a tuple can't be changed once made, so a failure's path stays as it was yielded. superstruct makes a new array at each level, `[...path, k]`, for the same reason.
