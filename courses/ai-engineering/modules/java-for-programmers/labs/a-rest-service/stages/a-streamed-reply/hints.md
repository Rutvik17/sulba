`sendResponseHeaders(200, 0)` starts a reply of any length, sent in chunks, and `out.flush()` sends what's been written so far.

---

A `switch` over a sealed interface's records, `case Agent.Text text -> ...`, needs no `default`: the compiler knows every kind of event.

---

Keep the deadline as `System.nanoTime() + gate.limit().toNanos()`, and give each `next` what's left of it, never less than zero.

---

`try (var reply = agent.reply(content)) { ... }` closes the reply however the block ends, and `try { ... } finally { gate.leave(); }` around it gives the place back.

---

When the caller hangs up, the next write to the reply throws `IOException`. Let it pass out of the handler: the `finally` still runs.
