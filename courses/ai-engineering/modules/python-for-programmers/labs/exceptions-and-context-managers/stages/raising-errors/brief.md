superstruct reports a value that fails with an error of its own, `StructError`, a kind of `TypeError`. `assert` throws it, `validate` returns it in a pair, and `is` answers whether a value passes. Here is the heart of `StructError`, trimmed:

```ts
class StructError extends TypeError {
  constructor(failure: Failure, failures: () => Generator<Failure>) {
    let cached: Array<Failure> | undefined
    const { message, ...rest } = failure
    const { path } = failure
    super(path.length === 0 ? message : `At path: ${path.join('.')} -- ${message}`)
    Object.assign(this, rest)
    this.failures = () => (cached ??= [failure, ...failures()])
  }
}
```

The starter holds the port so far: `Failure`, and structs whose `failures` yields each failure as it's asked for. Write:

```
StructError(failure, rest) -> a TypeError with superstruct's message for failure, its
    value, path, key, type and refinement, and failures() giving failure and then each
    of rest, found the first time they're asked for
assert_(value, struct) -> None, or raises the StructError of value's first failure
validate(value, struct) -> (None, value) when value passes, or (error, None)
is_(value, struct) -> whether value passes
```

`raise` is JavaScript's `throw`. `try` ... `except StructError as error:` is its `try` ... `catch (error)`, with the class of error it handles named in the clause, where JavaScript's `catch` takes every error and tells them apart with `instanceof`. An `except` clause handles its class and every subclass of it. An `else` clause after the `except` clauses runs when the `try` clause raised nothing.

`super().__init__(message)` gives the error its message, which `str(error)` returns. `assert` and `is` are keywords in Python, so the port's names end in an underscore, the convention PEP 8 gives for a name that clashes with a keyword.
