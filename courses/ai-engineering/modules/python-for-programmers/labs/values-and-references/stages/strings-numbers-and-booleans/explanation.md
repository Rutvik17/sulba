```python
def is_number(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    return isinstance(value, int) or not math.isnan(value)


def integer(value):
    if is_number(value) and (isinstance(value, int) or value.is_integer()):
        return None
    return f"Expected an integer, but received: {value!r}"
```

Python's booleans are a subtype of its integers: `True + True` is `2`. A check written as `isinstance(value, (int, float))`, which is true for an instance of either class, would take a checkbox's `true` for a measurement, so the port rules booleans out before it looks for numbers.

NaN is a float, `float("nan")`. JSON has no NaN or infinity, and JavaScript's `JSON.parse` rejects them, but Python's `json.loads` reads `NaN` and `Infinity`: the service can receive them even though the form never sends them. superstruct rejects NaN and takes infinity for a number, and so does the port.

JSON's `3.0` arrives as a float, and to JavaScript it is the integer `3`, so the port takes a float with no fraction for an integer, as `Number.isInteger` does.
