Some of a model's failures pass: a server still loading its model, a provider with too many requests at once, a dropped connection, a reply that never comes. The shop's assistant should ask again then, but a customer is waiting, so it has a deadline. This stage writes the client the assistant will use, with httpx's `AsyncClient`.

In `retry.py`, write `ask_within(client, messages, max_tokens, deadline, timeout, jitter)`. It sends the request `ask` sends and returns its `Reply`, and when the request fails:

- After a `408`, `409`, `429` or any `5xx`, a timeout (`httpx.TimeoutException`) or a lost connection (`httpx.NetworkError` or `httpx.RemoteProtocolError`), it waits and asks again.
- After any other error status, it raises `ModelError` at once, with the status and the error's message.
- It waits as many seconds as the response's `Retry-After` header gives, when the header is a number. Otherwise it waits {% $fig.first %} second after the first attempt, twice as long after each attempt after that, and at most {% $fig.most %} seconds, each of these waits multiplied by `0.5 + jitter() / 2`.
- Each attempt waits at most `timeout` seconds for its reply.
- It's done within `deadline` seconds of the call. An attempt never waits past the deadline, and when the next wait would end at or past it, `ask_within` raises `GaveUp` from the last failure, with `raise GaveUp(...) from error`.

Measure time with the event loop's clock, `asyncio.get_running_loop().time()`, and wait with `asyncio.sleep`.

```
await ask_within(client, messages, max_tokens, deadline, timeout=20, jitter=random.random) -> Reply
```

Two tests run on every attempt. Then five checks run before the code ships.
