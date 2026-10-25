`vars(record)` holds every attribute of a record, the `extra` fields among them. `STANDARD` in the starter holds the ones every record has.

---

`request_id.set(id)` gives a token, and `request_id.reset(token)` in a `finally` puts back what was there. Each request runs in its own task with its own copy of the context, so requests answered at once keep their own ids.

---

The middleware passes the app its own `send`, which adds the header to the `http.response.start` message's `headers` and keeps its `status` before it calls the real one.
