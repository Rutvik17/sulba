```python
def cached(size):
    def decorate(check):
        remembered = functools.lru_cache(maxsize=size, typed=True)(check)

        @functools.wraps(check)
        def caching(value):
            if isinstance(value, (list, dict)):
                return check(value)
            return remembered(value)

        return caching

    return decorate
```

`cached(size)` is a decorator factory, as `define(name)` is: it returns the decorator, which returns the check. `lru_cache` is a decorator too, called here as a function on `check`. It keeps its results in a dict, so its arguments must be hashable, and lists and dicts go straight to `check`.

A dict gives equal values one entry, and `1`, `1.0` and `True` are equal in Python, so a cache keyed by the value alone would hand `True` the message it kept for `1.0`. With `typed=True`, `lru_cache` keeps arguments of different types apart, and a cache of your own would key on `(type(value), value)` for the same reason.

When the cache is full, `lru_cache` forgets the result used longest ago, so the codes the day keeps coming back to stay in it, and its memory has a limit however many codes arrive.
