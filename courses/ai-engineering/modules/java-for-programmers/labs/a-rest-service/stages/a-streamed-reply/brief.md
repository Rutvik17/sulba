The desk's agent writes its reply a piece at a time, and the lab gives it to you as an interface, `Agent.java`. `agent.reply(message)` starts a reply and gives an `Agent.Reply`, whose `next(wait)` gives each event as it comes, or throws `TimeoutException` if none comes within `wait`. An event is one of three records of the sealed interface `Agent.Event`: a `Text` carries a piece of the reply's text, a `Tool` names a tool the agent runs, and a `Done`, the last, carries the whole reply. A reply the model fails throws `Agent.Failed`, and closing a reply stops the agent writing it.

In `Replies.java`, write `Replies`, an `HttpHandler` that a server gives `/messages`, and that answers `POST /messages` with the agent's reply as server-sent events, through your gate.

- The body is a `Say`, `{"content":"Where's my replacement card?"}`, read with `Api.JSON`. Its content, without the spaces at its ends, is the message: from 1 to 2,000 characters, or a 422 with the detail `A message is 1 to 2,000 characters, without the spaces at its ends.` A body that isn't JSON, or doesn't fit, gets the problem `Problems.of` gives, and a `Content-Type` that isn't `application/json` gets the same 415 as your API's.
- Any other path gets a 404, and any other method a 405 with `Allow: POST`, as problem details.
- The reply takes a place at the gate first. When the line is full, it's a 503 with the detail `The desk is answering as many callers as it can.` and the gate's `Retry-After`, and the agent isn't asked.
- The reply is `text/event-stream`, and each event goes to the caller as it comes. A `Text` is a `text` event, `{"delta": ...}`; a `Tool` is a `tool` event, `{"name": ...}`; and a `Done` is a `done` event, `{"content": ...}`, which ends the reply:

  ```
  event: text
  data: {"delta":"Your card"}

  ```

- A reply has the gate's limit, counted from when it starts. Past it, the reply ends with an `error` event, `{"title":"The reply took too long."}`. When the model fails, it ends with `{"title":"The desk couldn't reply."}`.

However the reply ends, at its `done`, at an error, or when the caller hangs up, the reply is closed and its place goes back to the gate.

```java
public record Say(String content)
public Replies(Agent agent, Gate gate)
public void handle(HttpExchange exchange) throws IOException
```

The tests' agents follow scripts, with pauses between their events, on threads of their own.
