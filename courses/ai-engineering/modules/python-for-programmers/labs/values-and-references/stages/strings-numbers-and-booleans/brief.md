The clinic's intake form, a web page in JavaScript, checks each breast mass sample with superstruct, a library for checking data, before it sends the sample to the screening service. The service is in Python and must check what arrives the same way, so this module ports superstruct to Python.

superstruct's simplest checks say whether a value is a string, a number or a boolean. In the port, a check is a function that takes a value and returns `None` when it passes, or a message saying why it doesn't. Here is superstruct's check for strings, and its port in the starter:

```js
(value) => typeof value === 'string' || `Expected a string, but received: ${print(value)}`
```

```python
def string(value):
    if isinstance(value, str):
        return None
    return f"Expected a string, but received: {value!r}"
```

`isinstance` asks whether a value is an instance of a class, and `and`, `or` and `not` are Python's `&&`, `||` and `!`. An f-string fills in what its braces hold, and `!r` writes the value as `repr` does, so a string keeps its quotes, as it does in superstruct's messages.

The service reads what the form sends with `json.loads`, which gives `dict`, `list`, `str`, `int`, `float`, `bool` and `None`. JavaScript has one type of number, where Python has two: JSON's `3` becomes the `int` `3`, and `3.0` the `float` `3.0`. An `int` has no size limit.

Write:

```
number(value) -> None for what JavaScript's typeof calls a number, other than NaN
integer(value) -> None for a number with no fraction, as Number.isInteger says
boolean(value) -> None for True or False
```

each with superstruct's message, such as:

```
Expected a number, but received: 'invalid'
Expected an integer, but received: 3.14
Expected a value of type `boolean`, but received: `'invalid'`
```

The tests port superstruct's own, and add the values where Python's types and JavaScript's part ways.
