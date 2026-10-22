A conversation with the desk's agent grows with every request. Each one sends the whole conversation again, with every tool result in it, and a search gives five passages. Qwen3.5-4B is served with a context of 16,384 tokens, and a conversation of a dozen questions fills it.

In `context.py`, write `Context`, which holds a conversation's messages after its system message, and keeps its requests within a budget of tokens:

- `add(message)` adds a message, and `request()` gives the messages the next request sends: the system message, `{"role": "system", "content": system}`, then each message added, in order.
- `count(usage)` keeps the size of the request just answered, from its usage: the tokens of its prompt and of its reply, which the next request sends again.
- `clear()` clears every tool result but the `keep` most recent. A cleared result's content is `CLEARED` with the name of the tool that gave it, from the call with its id; the calls, their ids and every other message stay as they were. It gives how many it cleared that weren't cleared before.
- `fit()` runs before each request: when the last request was over the budget, it clears, and gives how many it cleared; otherwise it gives 0.

```
Context(system, budget, keep=2)
```
