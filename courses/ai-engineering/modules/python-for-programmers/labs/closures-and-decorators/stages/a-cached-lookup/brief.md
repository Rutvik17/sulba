Each sample's code must belong to a patient the clinic's registry knows, and the registry's check is slow. A day's records repeat their codes, so the service keeps the registry's answers and asks again only about a code it hasn't kept. Write:

```
cached(size) -> a decorator that keeps a check's messages for up to size values,
    forgetting the one used longest ago when it's full
```

A cached check gives the same message as its check for every value, and calls its check only for a value it hasn't kept. It keeps its check's name and docstring.

`True == 1 == 1.0` in Python, and their hashes are equal, so a dict holds all three under one key. The checks tell booleans apart from numbers, so the cache must too. A value that can't be a dict's key, such as a list or a dict, goes to the check each time.

`functools.lru_cache(maxsize=size, typed=True)` makes a function that keeps the results of the last `size` calls, and `typed=True` keeps arguments of different types apart. Or keep the messages in a dict of your own. Hidden tests check what a cached check gives, and three checks test it before it ships.
