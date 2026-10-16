```python
def refine(check, name, test):
    def refined(value):
        message = check(value)
        if message is not None:
            return message
        result = test(value)
        if result is True:
            return None
        if isinstance(result, str):
            return result
        return (
            f"Expected a value of type `{check.__name__}` with refinement `{name}`, "
            f"but received: `{value!r}`"
        )

    refined.__name__ = check.__name__
    return refined
```

`min_` makes its test as a closure of its own, over `threshold` and `exclusive`, and hands it to `refine`, which wraps it in another. Stacked refinements are closures inside closures: `min_(max_(number, 30), 5)` calls the `max_` check, which calls `number`, before its own test runs.

Python's `or` gives back one of its operands, as JavaScript's `||` does, so a test written as `v > 0 or "Not positive"` gives `True` or the message.

In superstruct's own `min`, `||` binds more tightly than `? :`, so an exclusive `min` returns a bare `false`, and superstruct gives its plain message for it. The port gives `min_`'s own message either way.
