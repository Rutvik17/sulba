```python
class Struct:
    def __or__(self, other):
        if not isinstance(other, Struct):
            return NotImplemented
        left = self.members if isinstance(self, Union) else (self,)
        right = other.members if isinstance(other, Union) else (other,)
        return Union([*left, *right])

    def __contains__(self, value):
        return self.validate(value) is None

    def __repr__(self):
        return f"{type(self).__name__}()"


class Union(Struct):
    def failures(self, value, path=()):
        found = [list(member.failures(value, path)) for member in self.members]
        if not all(found):
            return
        shown = " | ".join(member.type for member in self.members)
        message = f"Expected the value to satisfy a union of `{shown}`, but received: {value!r}"
        yield Failure(path, self.type, message)
        for failures in found:
            yield from failures
```

`NotImplemented` tells Python that this method can't do the operation, so Python tries the other operand's reflected method, `__ror__`, before it raises a `TypeError`. Raising the `TypeError` in `__or__` would end the search early, and a class written later couldn't join itself to a struct with a `__ror__` of its own.

`a | b | c` runs as `(a | b) | c`, so its left side is already a union. Taking the members of each side makes one union of three, as `union([a, b, c])` is, whose message names `string | number | array` rather than a union inside a union.

`Union` replaces `failures` instead of `test`, because its failure depends on its members' failures, and superstruct reports those too, after its own.

`type(self).__name__` is the name of the instance's own class, so a subclass shows its own name without a `__repr__` of its own: `Type({})` shows as `Type({})` through `Object`'s method. The data model asks that a `__repr__` look like the Python expression that makes the object, where it can, and these do.
