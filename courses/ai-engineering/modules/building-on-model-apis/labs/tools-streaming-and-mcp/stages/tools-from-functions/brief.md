The shop's assistant can do more than answer from what it knows: it can look up the shop's hours, price a repair or find a booking, with the shop's own Python functions. The model doesn't run them. A request lists the tools the model may use, each with a JSON Schema of its parameters, and the model's reply asks for a call, naming a tool and giving its arguments as JSON. The code runs the call and sends the result back. This stage writes both ends.

In `tools.py`, write `describe(function)`, the tool a function is:

```json
{
  "type": "function",
  "function": {
    "name": "opening_hours",
    "description": "The shop's opening hours on a day of the week.",
    "parameters": {
      "type": "object",
      "properties": {"day": {"type": "string", "enum": ["Monday", "Tuesday", "...", "Sunday"]}},
      "required": ["day"],
      "additionalProperties": false
    },
    "strict": true
  }
}
```

- The name is the function's. The API takes names that match `[a-zA-Z0-9_-]{1,64}`, so raise `ValueError` for any other.
- The description is the function's docstring, as `inspect.getdoc` gives it.
- Each parameter's schema comes from its type: `str` a string, `int` an integer, `float` a number, `bool` a boolean, `list[X]` an array whose items have X's schema, `Literal` of strings a string from an `enum` of them, `X | None` X's schema with `"null"` among its types and in its `enum`, and `Annotated[X, "text"]` X's schema with the text as its `description`. Raise `TypeError` for any other type.
- Every parameter is required, and no other is allowed, as `strict` asks.

Then write `run(functions, call)`, which answers a tool call from the model's reply with the message the API takes back: the role `tool`, the call's id as `tool_call_id`, and as `content`, the function's value as JSON. A call that can't run never raises: its content is `{"error": ...}` with what went wrong, for the model to read. That's a name with no function, arguments that aren't JSON, an object without exactly the function's parameters, or an exception the function raises.

```
describe(function) -> dict
run(functions, call) -> {"role": "tool", "tool_call_id": ..., "content": ...}
```
