`client.post("/chat/completions", json=body)` sends `body` as JSON, with its `Content-Type`, to the path under the client's base URL.

---

`response.is_error` is true for any `4xx` or `5xx` status, and `response.json()` reads the body.

---

`response.json()` raises `ValueError` when the body isn't JSON. Catch it, and the `KeyError` of JSON without an `error`, and fall back to `response.text`.
