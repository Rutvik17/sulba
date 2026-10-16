superstruct's `run` walks a value and its struct together, finding each failure and the path to it. It's a generator function, marked by its `*`: it yields each failure as it finds it, and goes on only when asked for the next. Here is the heart of it, trimmed:

```js
function* run(value, struct, options = {}) {
  const { path = [] } = options
  for (const failure of struct.validator(value)) yield [failure, undefined]
  for (const [k, v, s] of struct.entries(value)) {
    for (const t of run(v, s, { path: [...path, k] })) {
      if (t[0]) yield [t[0], undefined]
    }
  }
}
```

Python's generators work the same way. A function with `yield` in it returns a generator when it's called, which runs the function's body as far as the next `yield` each time it's asked for a value, by `next` or a `for` loop. `yield from other` yields each value another generator yields. Write:

```
failures(value, schema, path=()) -> each failure of value against schema, as a
    (path, message) pair, in superstruct's order
```

As superstruct does:

- an object's fields come in the schema's order, then the fields the schema doesn't know, in the value's order, each with the message `never` in the starter gives;
- an array's items come in their order;
- a tuple's items come in their order, and an item past the schema's last is unknown, as an unknown field is;
- a value that isn't a dict for an object, or a list for an array or a tuple, fails as a whole, with `Expected an object, but received: ...`, `Expected an array value, but received: ...` or `Expected an array, but received: ...`, and nothing inside it is checked.

A field or a tuple's item that the value leaves out fails with `Missing`, where superstruct passes `undefined` to its check.
