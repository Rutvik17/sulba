```python
def array[T](item: Struct[T]) -> Struct[list[T]]:
    def test(value: object) -> TypeGuard[list[T]]:
        return isinstance(value, list) and all(item.test(each) for each in value)

    return Struct("array", test)


def create[T](value: object, struct: Struct[T]) -> T:
    if struct.test(value):
        return value
    raise StructError(
        f"Expected a value of type `{struct.name}`, but received: `{value!r}`"
    )
```

mypy works out each `T` from the call: `array(nullable(string()))` is a `Struct[list[str | None]]`, so `create(record, array(nullable(string())))` is a `list[str | None]`, and code that uses it as anything else fails the check. superstruct gets the same from TypeScript, and its `Infer` type reads `T` back out of a struct.

`TypeGuard` narrows only where the test returns `True`, so the rest of the code keeps its full type: after `is_(value, string())` returns `False`, `value` may still be a string, because a struct's test can reject values of its own type, as `number` rejects NaN. A predicate typed with `TypeIs` would tell mypy otherwise, and mypy would treat what's left as certain.
