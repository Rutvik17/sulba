`await client.post("/chat/completions", json=body, timeout=seconds)` gives one request its own timeout, and `except (httpx.TimeoutException, httpx.NetworkError, httpx.RemoteProtocolError) as error:` catches the failures of the connection.

---

Keep the deadline as a time on the loop's clock, `end = loop.time() + deadline`, so the time left is always `end - loop.time()`.

---

`response.headers.get("retry-after", "")` is the header's text, and `.isdigit()` tells a number of seconds from a date.
