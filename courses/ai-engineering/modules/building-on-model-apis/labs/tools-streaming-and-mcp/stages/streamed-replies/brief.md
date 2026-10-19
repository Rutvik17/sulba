A model writes its reply a token at a time, and a customer shouldn't wait for the last word to read the first. With `"stream": true`, the API sends the reply as it's written, as server-sent events: each a line of `data: ` and a chunk of JSON, then a blank line, and `data: [DONE]` at the end.

```
data: {"choices": [{"index": 0, "delta": {"role": "assistant", "content": null}, "finish_reason": null}]}

data: {"choices": [{"index": 0, "delta": {"content": "Let me check."}, "finish_reason": null}]}

data: {"choices": [{"index": 0, "delta": {"tool_calls": [{"index": 0, "id": "call_1", "type": "function", "function": {"name": "opening_hours"}}]}, "finish_reason": null}]}

data: {"choices": [{"index": 0, "delta": {"tool_calls": [{"index": 0, "function": {"arguments": "{\"day\": \"Sat"}}]}, "finish_reason": null}]}

data: {"choices": [{"index": 0, "delta": {"tool_calls": [{"index": 0, "function": {"arguments": "urday\"}"}}]}, "finish_reason": null}]}

data: {"choices": [{"index": 0, "delta": {}, "finish_reason": "tool_calls"}]}

data: {"choices": [], "usage": {"prompt_tokens": 80, "completion_tokens": 30, "total_tokens": 110}}

data: [DONE]
```

Each chunk's `delta` adds a piece to the reply: a piece of its text, or a piece of a tool call, which its `index` names, its `id` and name first and its arguments after. The reason the reply finished comes in the last chunk with a choice. With `"stream_options": {"include_usage": true}`, the tokens it used come after, in a chunk with no choices.

In `stream.py`, write `stream(client, messages, tools=None, on_text=...)`. Post `messages` with `model`, `"stream": true`, those `stream_options`, and `tools` when there are any, through `client.stream`, and read the reply as its bytes arrive:

- A line ends at CR LF, at LF or at CR, and nowhere else, so a reply's text can hold other kinds of line break.
- A blank line ends an event. A line that starts with `:` is a comment. A `data` line's value is what follows its colon, less one space after it, and an event with several `data` lines joins their values with line breaks.
- Hand each piece of text to `on_text` as it arrives.

Return a `Streamed`: the text, the tool calls as a whole reply has them, in the order of their index, the reason the reply finished, and the usage, or `None` when none came. When the API answers with an error, raise `ModelError` with its status and message.

The tests compare your replies with the ones the openai package puts together from the same streams.

```
stream(client, messages, tools=None, on_text=...) -> Streamed
```
