In superstruct, a struct is made by calling a function, such as `literal(42)` or `size(string(), 1, 5)`, and it remembers what it was made with. Each is a closure: a function made inside another function, which keeps the variables of the function that made it.

```js
function literal(constant) {
  const description = print(constant)
  return new Struct({
    type: 'literal',
    validator(value) {
      return value === constant || `Expected the literal \`${description}\`, but received: ${print(value)}`
    },
  })
}
```

Python's functions are values, as JavaScript's are. A function can make another with `def` and return it, and the one it returns keeps the names it uses from the function that made it. Write factories that each return a check:

```
literal(constant) -> a check that passes only constant
enums(options) -> a check that passes only the options, as they were when it was made
nullable(check) -> a check that passes None as well as what check passes
size(check, low, high=None) -> a check that passes what check passes when its size,
    a number's value or the length of a string or a list, is from low to high, or is
    low when there is no high
```

`same`, in the starter, is JavaScript's `===` from the first lab. A `size` check gives `check`'s own message first, and measures only a value `check` passes. Its messages name `check`'s type, which is its `__name__`:

```
Expected a number between `1` and `5` but received `0`
Expected a string with a length of `4` but received one with a length of `3`
```
