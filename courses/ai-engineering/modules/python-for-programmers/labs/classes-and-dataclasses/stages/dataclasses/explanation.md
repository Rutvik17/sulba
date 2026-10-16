```python
@dataclass(frozen=True)
class Failure:
    path: tuple
    type: str
    message: str
    refinement: str | None = None

    @property
    def key(self):
        return self.path[-1] if self.path else None
```

`@dataclass` reads the fields from the class body's annotations, in order, and writes the methods a JavaScript class would have to write by hand: `__init__` to set them, `__repr__` to show them and `__eq__` to compare them. Python calls these methods itself, for `Failure(...)`, `repr(failure)` and `==`: names with two underscores at each end are kept for methods like these.

With `frozen=True`, setting a field raises `FrozenInstanceError`. Since a frozen failure can't change, the decorator writes `__hash__` too, from its fields, so equal failures land in one place in a set or a dict. A dataclass that isn't frozen, and compares by its fields, gets no hash: changing a field would change its place.

`key` is computed from `path`, so it's a property rather than a field: it can never disagree with the path.
