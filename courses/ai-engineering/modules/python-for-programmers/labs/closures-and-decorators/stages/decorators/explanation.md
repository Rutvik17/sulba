```python
def counted(check):
    @functools.wraps(check)
    def counting(value):
        message = check(value)
        if message is not None:
            counting.failed += 1
        return message

    counting.failed = 0
    return counting
```

A decorator runs once, when the `def` under it runs, and the name is given whatever it returns. Without `functools.wraps`, the check `counted` returns would be named `counting` and have no docstring, and every message built from its `__name__` would name it `counting`. `wraps` copies the check's name and docstring, among other details, and adds a `__wrapped__` attribute that leads back to it.

The count lives on the function `counted` returns, so each call to `counted` makes a new function with its own count. A count kept in one place for all of them, or keyed by the check's name, would add up the radius's failures with every other number's. A closure can also keep a count in a variable of the function that made it, but needs `nonlocal count` before it can assign to it: without it, `count += 1` makes `count` a local variable of the inner function, which fails on its first use.
