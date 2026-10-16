```python
def enums(options):
    options = tuple(options)
    shown = ",".join(repr(option) for option in options)

    def check(value):
        if any(same(value, option) for option in options):
            return None
        return f"Expected one of `{shown}`, but received: {value!r}"

    return check
```

Each call to `enums` runs its body again, so each check it returns has its own `options` and its own `shown`, worked out once, when the check is made, rather than at each call.

A closure keeps the variables of the function that made it, not their values at the moment it was made. Without the copy, `options` would name the caller's list, and a list the caller changed later would change the check too. superstruct's own `enums` keeps the array it's given, so in JavaScript a change to the array changes what the struct passes, but not its message.
