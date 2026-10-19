With tools, the assistant answers in rounds. It sends the conversation with the tools, and the model either answers, with `finish_reason` `stop`, or calls tools, with `tool_calls`:

```json
{
  "message": {
    "role": "assistant",
    "content": null,
    "tool_calls": [
      {"id": "call_1", "type": "function", "function": {"name": "opening_hours", "arguments": "{\"day\":\"Saturday\"}"}},
      {"id": "call_2", "type": "function", "function": {"name": "repair_price", "arguments": "{\"service\":\"brakes\",\"bikes\":1}"}}
    ]
  },
  "finish_reason": "tool_calls"
}
```

The code runs each call, then asks again with the conversation, the model's message with its calls, and each call's result in a message with the role `tool` and the call's id, in the calls' order. The model reads the results and answers, or calls again.

In `loop.py`, write `answer(client, messages, functions, rounds=4, max_tokens=512)`. Send `messages` with `model`, `max_completion_tokens` and `tools`, each of `functions` as your `describe` gives it, and run the calls with your `run`, which never raises: a call that fails goes back to the model as an error it can read.

Return the model's answer. Raise `NoAnswer` when the model still calls tools after `rounds` requests, or when a reply finishes for any reason but `stop` or `tool_calls`, and `ModelError` when the API answers with an error. Leave the caller's `messages` as they were.

```
answer(client, messages, functions, rounds=4, max_tokens=512) -> str
```
