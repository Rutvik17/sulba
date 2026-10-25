The agent in `agent.py` gives its reply as events, as the model writes it. A `Text` event carries each piece of the reply's text, a `Tool` event names each tool it runs, and a `Done` event carries the whole reply. In `replies.py`, send those events on to the caller as server-sent events, through your gate.

- `Say` is the message's body: `content`, from 1 to 2,000 characters once the spaces at its ends are stripped, and no other field.
- `Agents(make)` keeps each conversation's agent. `of(conversation)` gives it, made with `make(conversation.page)` on the conversation's first message and kept for the rest. `replying` holds the ids of the conversations a reply is running in.
- `found(conversation_id, conversations)` gives the conversation, or raises a 404 with the detail `There's no conversation with this id.`
- `turn(say, request, conversation)`, a dependency, gives the `Turn` once the message fits and the conversation is found. While a reply is running in the conversation, it raises a 409 with the detail `The desk is still replying in this conversation.` Otherwise it marks the conversation replying and takes a place at the gate. When the line is full, it raises a 503 with the detail `The desk is answering as many callers as it can.` and the gate's `Retry-After`. When no place comes, because the line is full or the caller left, the conversation is no longer marked replying.

Then `POST /conversations/{conversation_id}/messages` sends the reply as it comes. It sends a `text` event, `{"delta": ...}`, for each piece, and a `tool` event, `{"name": ...}`, for each tool. Then the conversation keeps the caller's message and the reply, and the route sends a `done` event, `{"content": ...}`, with the whole reply. The reply has the gate's `seconds`:

- past them, it ends with an `error` event, `{"title": "The reply took too long."}`;
- when the model fails, with `ModelError`, `OutOfRounds` or an `httpx.HTTPError`, it ends with `{"title": "The desk couldn't reply."}`.

A reply that doesn't finish is kept nowhere: not in the conversation, and not in the agent's `messages`, so the model never reads it. However the reply ends, the conversation takes a message again and the place goes back to the gate.

The app keeps its conversations at `request.app.state.conversations`, its agents at `request.app.state.agents` and its gate at `request.app.state.gate`.

```
Agents(make).of(conversation) -> Agent
found(conversation_id, conversations) -> Conversation
turn(say, request, conversation) -> Turn
POST /conversations/{conversation_id}/messages
```

The tests' agents call a scripted model, whose replies can take minutes on the tests' clock.
