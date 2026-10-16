The service checks each sample's record as a whole, as superstruct checks an object against a struct for each of its fields. In the port, a schema is plain Python data:

```python
SAMPLE = {
    "id": string,
    "radius": number,
    "tags": [string],
    "position": (number, number),
}
```

A function is a check of one value, as in the first lab. A dict is an object, with a schema for each field. A list holding one schema is an array whose items each match it, and a tuple of schemas is an array with one item for each. The starter holds the checks for strings, numbers and booleans.

superstruct makes new structs from old ones: `pick` keeps some fields, `omit` drops some and `assign` joins several. Each is a loop over the fields in JavaScript:

```js
const subschema = {}
for (const key of keys) {
  subschema[key] = schema[key]
}
```

Python builds a list, a dict or a set from a loop in one expression, a comprehension: `[f(x) for x in xs if g(x)]` is JavaScript's `xs.filter(g).map(f)`, and `{key: value for key, value in pairs}` builds a dict. Write:

```
pick(schema, keys) -> a schema of schema's fields named in keys, in the order of keys
omit(schema, keys) -> a schema of the fields of schema not named in keys, in schema's order
assign(*schemas) -> one schema with the fields of all of schemas, a later field winning
explain(path, message) -> superstruct's message for a failure at path
```

`*schemas` gathers any number of arguments into a tuple, as `...schemas` gathers them into an array in JavaScript. A failure's path is a tuple of the keys and indexes that lead to its value, such as `("tags", 1)`, and superstruct's message joins them with dots:

```
At path: tags.1 -- Expected a string, but received: False
```

A failure at the top of a value has no path, and its message is the message alone.
