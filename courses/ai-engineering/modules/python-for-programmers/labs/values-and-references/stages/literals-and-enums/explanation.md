```python
def same(a, b):
    if isinstance(a, (list, dict)) or isinstance(b, (list, dict)):
        return a is b
    if isinstance(a, bool) or isinstance(b, bool):
        return isinstance(a, bool) and isinstance(b, bool) and a == b
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return a == b
    return type(a) is type(b) and a == b
```

`==` compares values and `is` compares objects. For lists and dicts, `is` is JavaScript's `===`. For numbers and strings, `is` only looks right: it holds for `42` in CPython, which keeps one object for each small integer, but `1000` read from JSON is a new object, and fails `is 1000` though it equals it. Python warns when it sees `is` beside a number or a string written in the code for that reason.

Python's `in` compares each item with `is`, then with `==`. So `True in [0, 1]` is true, and whether NaN is `in` a list depends on whether it's the same NaN object. `enums` goes through the options itself instead, with `same` and a test for NaN.
