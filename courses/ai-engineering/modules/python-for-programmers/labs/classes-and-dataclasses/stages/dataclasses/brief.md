This lab ports superstruct's structs to classes, as the original has them, starting with what a check reports. superstruct describes each failure as an object of this shape:

```ts
type Failure = {
  value: any
  key: any
  type: string
  refinement: string | undefined
  message: string
  explanation?: string
  branch: Array<any>
  path: Array<any>
}
```

The port keeps the path, the type, the message and the refinement, and works the key out from the path.

A Python class is much like a JavaScript one: its methods take the instance as their first argument, `self` by convention, where JavaScript has `this`. A method marked `@property` is read as an attribute, as a JavaScript getter is.

A class that only holds data is a dataclass. The `@dataclass` decorator writes `__init__`, `__repr__` and `__eq__` from the fields the class lists with their types, so `Failure(("age",), "number", message)` makes one and two with the same fields are equal. `frozen=True` makes its instances unchangeable, and so able to go in a set. Give `Failure` its fields, in this order:

```
path: tuple                    the keys and indexes that lead to the value
type: str                      the type of the struct the value failed
message: str                   superstruct's message
refinement: str | None = None  the refinement the value failed, if any
```

and write:

```
key -> the key or index of the value in the one around it, or None at the top
explain() -> superstruct's message, with "At path: ... -- " before it for a value
    below the top
```
