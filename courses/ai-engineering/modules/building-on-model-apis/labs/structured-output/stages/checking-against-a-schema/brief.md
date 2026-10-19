The bicycle repair shop's assistant reads customers' emails and fills in bookings for the shop's calendar, which takes them as JSON. Before a booking goes in, the assistant checks it against the calendar's JSON Schema, the standard way to say what a JSON value must look like:

```json
{
  "type": "object",
  "properties": {
    "name": {"type": "string", "minLength": 1, "maxLength": 60},
    "bike": {"enum": ["road", "mountain", "city", "cargo", "e-bike"]},
    "service": {"enum": ["puncture", "brakes", "gears", "full service"]},
    "date": {"type": "string", "format": "date"},
    "time": {"type": "string", "pattern": "^(09|1[0-6]):[03]0$"},
    "bikes": {"type": "integer", "minimum": 1, "maximum": 3},
    "phone": {"type": ["string", "null"], "pattern": "^\\+?[0-9 ]{7,15}$"},
    "notes": {"type": "string", "maxLength": 500}
  },
  "required": ["name", "bike", "service", "date", "time", "bikes", "phone", "notes"],
  "additionalProperties": false
}
```

In `schema.py`, write `errors(value, schema)`, which lists every way `value` fails `schema`, and nothing when it passes. Each `Error` has:

- `path`: where in `value` it fails, as a JSON path: `$` for the whole value, `$.bikes` for a key, `$.bikes[0]` for an item, and `$['wheel size']` for a key that isn't a letter followed by letters, digits and underscores;
- `keyword`: the keyword it fails, such as `required`;
- `message`: what's wrong, naming the value, the key or the rule, for a person or a model to act on.

Check these keywords, as JSON Schema 2020-12 defines them:

- `type`: a type, or a list of types any of which will do: `null`, `boolean`, `integer`, `number`, `string`, `array` or `object`. An `integer` is any number with no fractional part, and `true` and `false` aren't numbers.
- `enum`, a list of the values allowed, and `const`, the one value allowed. Two values are equal when they have the same type and the same value, numbers by their value.
- `properties`, each key's schema, `required`, the keys an object must have, and `additionalProperties`, which is `false` when no other key is allowed, or a schema for the other keys' values. One error says which keys aren't allowed.
- `items`, the schema of every item in an array, `minItems` and `maxItems`.
- `minimum` and `maximum`.
- `minLength` and `maxLength`, counted in characters, and `pattern`, a regular expression found anywhere in the string, as `re.search` finds it.

Each keyword checks only values of its type: `minimum` passes a string, and `required` passes a list. `format` checks nothing: it's a note for the application.

The tests compare your errors' paths and keywords with jsonschema's, the Python library's, on {% $fig.cases %} recorded cases in `references/validation.json`.

```
errors(value, schema, path="$") -> list[Error]
```
