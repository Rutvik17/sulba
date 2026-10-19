The API keeps nothing between requests. Each one carries the whole conversation, the shop's instructions in the system message included, and the model reads all of it again, so a conversation's tenth question costs more than its first. The next stage counts those tokens.

`finish_reason` says why the model stopped: `stop` when it finished its answer, `length` when it reached `max_completion_tokens`, and `tool_calls` when it asked to call a tool. A reply cut off at `length` reads like a whole one up to its last words, so code that shows replies to customers checks it first. `max_completion_tokens` is the limit's name in OpenAI's API reference, which marks the older `max_tokens` as deprecated. llama.cpp's server reads both.

An error's status says what to do about it. A `400` means the request is wrong, a `401` or `403` the key, and a `404` the path or the model's name: the same request gets the same answer again. A `429` asks the client to slow down, and a `500` or `503` is the server's own trouble, which may pass, so the lab's last stage retries those. llama.cpp's server answers every request with a `503` and "Loading model" until its model is loaded, and with a `400` when a message has no `content`, as the tests show.

With the lab's model running, from `uv run sulba.py model` in another terminal, your code can ask it:

```python
import httpx

from chat import ask

with httpx.Client(base_url="http://127.0.0.1:9931/v1", timeout=60) as client:
    print(
        ask(
            client,
            [{"role": "user", "content": "How often should I oil my chain?"}],
            200,
        )
    )
```

Its words differ from one computer to the next, which is why the tests call a scripted model instead.
