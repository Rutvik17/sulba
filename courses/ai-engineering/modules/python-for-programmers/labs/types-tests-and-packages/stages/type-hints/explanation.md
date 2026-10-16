```python
def check_number(value: object) -> str | None:
    if (
        isinstance(value, bool)
        or not isinstance(value, int | float)
        or math.isnan(value)
    ):
        return f"Expected a number, but received: {value!r}"
    return None


class Sample(TypedDict):
    id: str
    radius: float
    note: NotRequired[str]
```

mypy reads the condition from left to right. By `math.isnan(value)`, the checks before it have ruled out every value that isn't an int or a float, so it accepts the call. With `value: Any`, it would have accepted `math.isnan(value)` with no check at all, and a string would have raised `TypeError` there as the service ran.

A `TypedDict` is checked only by the type checker: at run time, `Sample` makes a plain dict, and a record with an extra key or a missing one is still a dict. That's why `failures` checks the record's values as they come in, and code that has passed them can be typed as taking a `Sample`. mypy then reports a call that leaves out `radius`, or reads a key a `Sample` doesn't have.
