```python
def assert_(value, struct):
    failures = struct.failures(value)
    first = next(failures, None)
    if first is not None:
        raise StructError(first, failures)


def validate(value, struct):
    try:
        assert_(value, struct)
    except StructError as error:
        return error, None
    else:
        return None, value
```

`raise` stops the function and passes the error up through each caller until a `try` statement handles it, as `throw` does. `validate` handles `StructError` alone, so an error a struct raises by mistake, such as a `ZeroDivisionError`, still reaches the caller: `except Exception` would have reported a bug as a value that failed. The `else` clause keeps `return None, value` out of the `try` clause, so the `except` clause covers only what `assert_` raised.

`StructError` keeps the generator after its first failure, as superstruct does, so a record with many failures costs no more than its first until `failures()` is called. Its list is built once and kept, since the generator can't be read twice.
