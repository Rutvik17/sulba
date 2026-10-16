```python
class Struct:
    type = "unknown"

    def failures(self, value, path=()):
        message = self.test(value)
        if message is not None:
            yield Failure(path, self.type, message)
            return
        for key, item, struct in self.entries(value):
            yield from struct.failures(item, (*path, key))


class Type(Object):
    type = "type"

    def entries(self, value):
        for key, item, struct in super().entries(value):
            if key in self.schema:
                yield key, item, struct
```

`failures` is written once, and calls `self.test` and `self.entries`, which each class gives its own. Python looks a method up on the instance's own class first, then on the classes it inherits from, so a `Number` tests as a number, and a `Type` takes its entries from `Object`'s and drops the unknown ones. superstruct's `run` walks a value the same way, with functions where the port has methods.

`type = "number"` in a class body is a class attribute, shared by every instance of the class, which suits a value that's the same for all of them. A schema differs from one struct to the next, so `__init__` sets it on the instance, as `self.schema`, from a copy of the dict it's given.
