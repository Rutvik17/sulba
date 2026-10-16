superstruct joins structs with a function: `union([string(), number()])` passes a value that passes any one of them. In Python, a class can give an operator a meaning with a special method, named with two underscores on each side: `a | b` calls `type(a).__or__(a, b)`, `x in a` calls `a.__contains__(x)`, `a[key]` calls `a.__getitem__(key)`, and `repr(a)` calls `a.__repr__()`. Add them to `Struct` and its subclasses:

```
a | b -> a Union of a's members and then b's, where a struct that isn't a union is its
    own one member
value in struct -> whether value passes struct
object[key] -> the struct of the field key in an Object or Type's schema
repr(struct) -> the struct as it's made, such as Object({'id': String()}) or
    String() | Number()
```

`a | b` joins only structs. When `__or__` is given another kind of value, it returns `NotImplemented`, and Python raises a `TypeError` once the other value has no way to join them either.

Then write `Union.failures`, as superstruct's union fails: no failure when the value passes any member, and otherwise one of type `union` at the value's path, with the message

```
Expected the value to satisfy a union of `string | number`, but received: True
```

followed by each member's failures, member by member.
