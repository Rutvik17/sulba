`ConnectionPool(url, kwargs={"autocommit": True}, configure=register_vector, open=False)`, then `pool.open(wait=True, timeout=10)` in the lifespan, runs `register_vector` on each new connection, so each one sends NumPy vectors as pgvector's.

---

A `def` endpoint can return `StreamingResponse(events(), media_type="text/event-stream")` from a generator of strings, each `event: piece\ndata: {...}\n\n`. Hold a pool connection in the generator, with `with pool.connection() as conn:`, so it's kept for the reply and given back when it ends.

---

`sessions.find(token)` gives the `Account` of the session cookie `SESSION_COOKIE` carries, with its `email`, or `None`.
