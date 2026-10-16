superstruct is written in TypeScript, and its types are part of what it gives a program: a `Struct<T>` checks values of type `T`, `create(value, struct)` returns a `T`, and where `is(value, struct)` returns true, TypeScript treats the value as a `T`. The port gets the same from mypy. Write:

```
Struct[T](name, test)  a check of values of type T, where test(value) is
                       True for a value that passes
string() -> Struct[str]
number() -> Struct[float]
array(item: Struct[T]) -> Struct[list[T]]
nullable(struct: Struct[T]) -> Struct[T | None]
is_(value: object, struct: Struct[T]) -> TypeGuard[T]
create(value: object, struct: Struct[T]) -> T
```

`string` and `number` are named `"string"` and `"number"`, and pass what `isinstance(value, str)` and `check_number` pass. `array` is named `"array"`, and passes a list whose every item passes `item`. `nullable` keeps its struct's name, and lets `None` through as superstruct's `nullable` lets `null` through. `create` returns the value when it passes, and otherwise raises `StructError`, a `TypeError` of the port's own, with superstruct's message:

```
Expected a value of type `array`, but received: `['S00001', 7]`
```

`class Struct[T]:` makes a generic class, as `class Struct<T>` does in TypeScript, and `def array[T](item: Struct[T]) -> Struct[list[T]]:` a generic function, whose `T` mypy works out from the struct each call is given. `Callable[[object], TypeGuard[T]]` is the type of a function that takes any value and returns whether it's a `T`: import `Callable` from `collections.abc` and `TypeGuard` from `typing` at the top of `typed.py`.

Where a function that returns `TypeGuard[T]` returns `True`, mypy treats its argument as a `T`, as TypeScript does with a predicate `value is T`. TypeScript also narrows where the predicate returns false, and so does a function that returns Python's `TypeIs[T]`. But `TypeIs` is only safe for a test that's `True` for every value of its type, and `number`'s test is `False` for NaN, a float.
