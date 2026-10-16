Each of the form's measurements has a range it must fall in. superstruct adds a test like that to a struct with a refinement. `refine` makes one from a struct, a name and a test, and the other refinements are made with it:

```js
function min(struct, threshold, options = {}) {
  const { exclusive } = options
  return refine(struct, 'min', (value) => {
    return exclusive
      ? value > threshold
      : value >= threshold ||
          `Expected a ${struct.type} greater than ${exclusive ? '' : 'or equal to '}${threshold} but received \`${value}\``
  })
}
```

A refinement tests only a value its struct has passed, so its test can count on the kind of value it gets. Write:

```
refine(check, name, test) -> a check that passes what check passes when test(value) is
    True, where test can give a message of its own in place of False
min_(check, threshold, exclusive=False) -> at least threshold, or more than it when exclusive
max_(check, threshold, exclusive=False) -> at most threshold, or less than it when exclusive
pattern(check, regex) -> what check passes when regex matches somewhere in it
```

The names end in an underscore so they don't hide Python's own `min` and `max`, the convention PEP 8 gives for a name that clashes with a keyword. superstruct keeps a refinement's name on each failure it reports, beside the message. A check gives only a message, so a test that gives anything but `True` or a message fails with one that names the refinement, and `min_`, `max_` and `pattern` give their own:

```
Expected a value of type `string` with refinement `email`, but received: `'invalid'`
Expected a number greater than or equal to 0 but received `-1`
Expected a number less than 0 but received `0`
Expected a string matching `/\d+/` but received 'invalid'
```

A refined check keeps its check's type, so that a refinement on top of another names `number` too: give it its check's `__name__`. A compiled regular expression's `search` finds a match anywhere in a string, as JavaScript's `test` does, and its `pattern` is its source.
