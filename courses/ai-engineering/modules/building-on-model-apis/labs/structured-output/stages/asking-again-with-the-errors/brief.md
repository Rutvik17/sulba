The assistant asks the model to fill in a booking from a customer's email. A chat request can ask for a reply held to a JSON Schema, with `response_format`:

```json
"response_format": {
  "type": "json_schema",
  "json_schema": {"name": "booking", "schema": {...}, "strict": true}
}
```

`strict` asks the server to hold the reply to the schema exactly. A reply can fail it all the same: it can be cut off at its token limit, and not every server holds replies to a schema. So the assistant checks each reply with your `errors`, and when one fails, tells the model what was wrong and asks again.

In `extract.py`, write `ask_for(client, messages, schema, name, attempts=3, max_tokens=512)`. Post `messages` to `/chat/completions` with `model`, `max_completion_tokens` and the `response_format` above, and read the reply's first choice:

- When its `finish_reason` is `length`, it was cut off. Don't read it: its problem is `The reply was cut off at its token limit.`
- When its text isn't JSON, its problem is `The reply isn't JSON: ` followed by the error `json.loads` raised.
- Otherwise, each error `errors` finds is a problem, written as its path, a colon and its message.

Return the value a reply with no problems holds. Otherwise, ask again with the conversation so far, the reply as the assistant's message, and a user's message that lists the reply's problems:

```
Your reply doesn't match the schema:
- $.time: '10.30' does not match '^(09|1[0-6]):[03]0$'
- $.bikes: '1' is not of type integer
Reply again with only the corrected JSON.
```

When none of `attempts` requests gets a reply that matches, raise `NoMatch` with the last reply's problems. When the API answers with an error, raise `ModelError` at once. Leave the caller's `messages` as they were.

```
ask_for(client, messages, schema, name, attempts=3, max_tokens=512) -> value
```
