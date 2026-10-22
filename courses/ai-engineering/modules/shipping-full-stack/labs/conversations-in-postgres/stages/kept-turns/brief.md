The desk's replies still keep their turns in memory. `replies.py` starts as you left it in The desk's API. Change it to keep each turn in the store, `request.app.state.conversations`, with what the turn used:

- `found` reads the conversation from the store. It's a `def` dependency, which FastAPI runs in its threadpool.
- `Agents.of` gives a conversation kept by an earlier run of the app an agent that goes on from its messages: each caller's message as a `user` message, and each of the desk's as an `assistant` message, after the agent's own.
- A turn that's done is kept, with its two messages and its usage, before its `done` event is sent, so a caller who reads the conversation then finds the reply in it.
- A turn that isn't done is kept too, with its usage and no messages: `too long` past the gate's time limit, `failed` when the model fails, and `left` when the caller leaves before the reply ends, which cancels the route's work.
- A turn's usage is when it started, from `datetime.now(UTC)`; its seconds, by the event loop's clock, `asyncio.get_running_loop().time()`; and the tokens the agent has counted, `agent.prompt_tokens` and `agent.completion_tokens`.
- The store's work runs in the threadpool, through `run_in_threadpool` from `starlette.concurrency`, never on the event loop.
- However the turn ends, the conversation takes a message again and the place goes back to the gate, as before.

```
POST /conversations/{conversation_id}/messages
```

The tests' agents call a scripted model, on the tests' clock.
