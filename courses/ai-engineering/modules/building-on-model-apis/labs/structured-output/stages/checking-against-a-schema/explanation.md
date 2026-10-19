A model held to a schema still sends JSON that fails it at times. OpenAI's guide to structured outputs names two cases: a refusal, which doesn't follow the schema, and a reply cut off at its token limit. Not every model or server holds replies to a schema either, so code that takes a model's JSON checks it before using it.

The cases the tests ran show where a schema says less than it seems to:

- `format` checks nothing by default. JSON Schema 2020-12 makes checking it something a validator must leave off unless asked, and recommends checking such values in the application. jsonschema leaves it off, so a booking for `2026-02-30`, or for `next Tuesday`, passes the calendar's schema.
- A `pattern` matches anywhere unless it's anchored, and jsonschema runs it with Python's `re.search`, in which `$` matches at the end of the string or just before a newline at its end. `"10:00\n"` passes the time's pattern.
- Without `"additionalProperties": false`, an object takes any other keys, and a reply can carry a `price` the calendar never asked for.
- A keyword checks only values of its own type, so a schema without `type` lets a string through `minimum` and a list through `required`.

So the code that takes a booking checks what the schema can't: that its date exists, and that the shop is open then. The schema checks the booking's shape.
