The screening service keeps a year of samples in memory, to compare each new sample with the ones before it, and drops the records the form sends twice. Each record becomes a `Sample`, made by a class method that checks the record with the class's struct. Write:

```
Sample.parse(record) -> a Sample of the record's fields, or a TypeError with the record's
    first failure, explained, as its message
```

A class method takes the class it was called on as its first argument, `cls` by convention, where a method takes the instance, so `cls(...)` makes an instance of that class. `cls(**record)` passes each of a dict's items as the argument of its key's name. superstruct's `create` throws a `StructError`, a kind of `TypeError`, with the message `explain()` gives, and `raise TypeError(message)` raises one in Python, as `throw new TypeError(message)` does in JavaScript.

`struct` in the class body has no type annotation, so it's a class attribute, which every sample shares, rather than a field. `@dataclass(frozen=True)` makes samples that can't be changed, with a hash from their fields. `slots=True` gives each sample fixed places for its fields, in `__slots__`, in place of a dictionary of its own, which takes less memory. Hidden tests check what `parse` gives, and three checks test `Sample` before it ships.
