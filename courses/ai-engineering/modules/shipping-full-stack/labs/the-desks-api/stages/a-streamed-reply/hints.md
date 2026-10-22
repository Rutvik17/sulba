A route with `response_class=EventSourceResponse`, from `fastapi.sse`, that yields `ServerSentEvent(event="text", data={"delta": delta})` sends each event as it's yielded, with its `data` as JSON.

---

A route that yields answers 200 whatever its body does, since FastAPI makes the response before the body's first event. A 404, 409 or 503 comes from a dependency, which runs before the response is made, so `found` and `turn` raise them, and the route itself only sends events.

---

Note how many messages the agent holds when the reply starts. `del agent.messages[before:]`, in the route's `finally`, forgets what the reply added, unless the `Done` event kept it. `StringConstraints(strip_whitespace=True, min_length=1, max_length=2000)` in `Annotated` holds `content` to its length.
