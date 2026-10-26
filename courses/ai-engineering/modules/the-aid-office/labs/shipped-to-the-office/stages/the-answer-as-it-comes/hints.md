`with client.stream("POST", "/chat/completions", json=body, timeout=TIMEOUT) as response:` opens the request, and `response.iter_lines()` gives the body's lines as they arrive. `raise_for_status()` works on it as on any response.

---

A generator can `yield` a verdict in its `except` block and `return`. Pieces it gave before then stay given: the verdict is what takes their place.
