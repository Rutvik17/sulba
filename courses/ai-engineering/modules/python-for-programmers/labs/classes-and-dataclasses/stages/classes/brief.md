superstruct's `Struct` is one class, and each kind of struct is made by a function that gives it a type and functions of its own. In the port, each kind of struct is a class of its own. `class Number(Struct):` makes a subclass, which has every method `Struct` has and can replace any of them with its own. Each struct has:

- `test(value)`, which gives `None` for a value of its kind, or superstruct's message;
- `entries(value)`, which gives each value inside a value that passed, with its key and its struct;
- `failures(value, path=())`, written once in `Struct` for every kind, which yields a `Failure` for a value the struct's `test` fails, and otherwise each failure of its entries.

Write `Struct.failures`, and `Struct.validate`, which gives the first failure or `None`. Then write the classes:

```
Number() -> what JavaScript's typeof calls a number, other than NaN
Object(schema) -> an object whose fields each pass their struct in schema; each field
    the schema doesn't know fails Never
Array(element) -> an array whose items each pass element
Type(schema) -> an Object whose fields the schema doesn't know pass, as superstruct's
    type does
```

with superstruct's types and messages: `number`; `object`, with `Expected an object, but received: ...`; `array`, with `Expected an array value, but received: ...`; and `type`, with the object's message. A field a value leaves out is `MISSING`, which shows as `undefined`, so its struct fails it as superstruct's would:

```
Expected a string, but received: undefined
```

`math.isnan` tells NaN apart: import `math` at the top of `structs.py` to use it. `__init__` is a class's constructor, as `constructor` is in JavaScript. `super()` reaches the class a method came from before a subclass replaced it: in `Type`, `super().entries(value)` calls `Object`'s.
