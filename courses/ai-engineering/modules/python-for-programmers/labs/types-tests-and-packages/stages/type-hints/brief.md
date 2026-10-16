The clinic's port goes into the service now, and the service's team checks every file with mypy before it's merged. TypeScript checks a program's types as it compiles it. Python never reads its annotations as it runs: a type checker reads them beforehand. Run with `--strict`, mypy reports every function whose parameters and return aren't all annotated. The tests run it over your file, and over code that calls your functions.

Write these, with the types shown:

```
Failure(path, message)  a frozen dataclass of
    path: tuple[str | int, ...]
    message: str
explain(failure: Failure) -> str
check_number(value: object) -> str | None
Sample                  a TypedDict of id: str and radius: float, and note: str,
                        which a record may leave out
label(sample: Sample) -> str
failures(record: dict[str, object]) -> list[Failure]
```

`explain` gives the message, after `At path: samples.2.radius -- ` when the path isn't empty, as the classes lab's did. `check_number` gives `None` for an int or a float other than NaN, and superstruct's message for anything else, `True` and `False` included, which JavaScript doesn't count as numbers:

```
Expected a number, but received: '17.99'
```

`label` gives `S00001 (17.99)`, and `S00002 (20.57): repeat` for a sample whose note is `"repeat"`. `failures` gives a failure for each field a `Sample` can't hold, in the order id, radius, note: an id that isn't a string, a radius that isn't a number, or a note there that isn't a string. A string's message is `Expected a string, but received: 7`.

`tuple[str | int, ...]` is a tuple of any length whose items are strings or ints. `object` is the type of every value, and mypy allows only what works on every value until code checks what a value is, as TypeScript does with `unknown`. Inside `if isinstance(value, str):`, mypy treats `value` as a string. `Any` switches checking off, as TypeScript's `any` does. A `str | None` has to be told apart from `None` before it's used as a string, as with TypeScript's `strictNullChecks`. A `TypedDict` is a dict with known keys, each with its own type, like a TypeScript object type: write it as a class whose body lists its keys with their types. `NotRequired[str]` marks a key a record may leave out, as `note?: string` does, and `sample.get("note")` gives its value or `None`.
