A bicycle repair shop wants an assistant that answers its customers' questions with a model. Whichever model it uses, from a provider or on the shop's own computer, serves the chat completions API, which OpenAI's API defines and llama.cpp's server, among others, serves too. A request is a `POST` to `/chat/completions` with the conversation as JSON, and the reply comes back as JSON. This stage makes that request by hand, with httpx.

In `chat.py`, write `ask(client, messages, max_tokens)`. `client` is an `httpx.Client` whose base URL is the API's, such as `http://127.0.0.1:9931/v1` for the lab's model. Post to `/chat/completions` a JSON body with:

- `model`: `MODEL`;
- `messages`: the conversation, a list of messages, each a dict with its `role`, `system`, `user` or `assistant`, and its `content`;
- `max_completion_tokens`: the most tokens the reply may take.

The reply's first choice holds the model's `message` and why it finished, and `usage` holds the tokens it read and wrote:

```json
{
  "choices": [
    {
      "index": 0,
      "message": {"role": "assistant", "content": "We open at 9 on Saturdays."},
      "finish_reason": "stop"
    }
  ],
  "usage": {"prompt_tokens": ..., "completion_tokens": ..., "total_tokens": ...}
}
```

Return them as a `Reply`. A reply that only calls a tool has no `content`, and its text is `""`.

When the API answers with an error status, raise `ModelError` with the status and the error's message. The API sends the message as JSON, `{"error": {"message": ...}}`, but something in between, such as a proxy, may answer with a page of its own: then the message is the body's text.

```
ask(client, messages, max_tokens) -> Reply
```
