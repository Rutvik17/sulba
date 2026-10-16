`string()` returns `Struct("string", is_string)`, where `is_string(value: object) -> TypeGuard[str]` returns `isinstance(value, str)`. `number`'s test can return `check_number(value) is None`.

---

`array` defines its test inside itself, `def test(value: object) -> TypeGuard[list[T]]:`, which reads `item` from the call that made it, and returns `Struct("array", test)`.

---

In `create`, `if struct.test(value): return value` returns a `T`: inside the `if`, mypy treats `value` as one.
