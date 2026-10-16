The clinic has checks superstruct doesn't, such as for a sample's code. superstruct's `define` makes a struct of a new type from a test that gives `true`, `false` or a message:

```js
const code = define('code', (value) => typeof value === 'string' && /^S\d+$/.test(value))
```

In Python, a function that takes a function and returns one can be written above a `def` as a decorator: `@counted` above `def side(value):` is the same as `side = counted(side)` after it. A decorator with arguments, such as `@define("code")`, is a call that returns the decorator. Write:

```
define(name) -> a decorator that makes a check of type name from a test
counted(check) -> check, counting in its failed attribute the values it has failed
```

```python
@define("code")
def code(value):
    """A sample's code: an S, then digits."""
    return isinstance(value, str) and value[:1] == "S" and value[1:].isdigit()
```

A `define` check passes what its test gives `True`, gives the test's message when it gives one, and otherwise fails as superstruct's does:

```
Expected a value of type `code`, but received: `'00123'`
```

The service will count each field's failures, so each counted check counts apart from the others. A check made by either keeps its test's or its check's docstring, and is named by its type, so that `size` and `min_` messages built on it name the type too. `functools.wraps` copies a function's name and docstring onto the function that wraps it: import `functools` at the top of `refine.py` to use it.
