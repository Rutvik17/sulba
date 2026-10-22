A tool message's `tool_call_id` is the `id` of a call in an earlier assistant message's `tool_calls`, and that call's `function` has the tool's `name`.

---

A result already cleared has `CLEARED`, with its tool's name, as its content, so comparing the two tells you whether to count it.

---

`results[: len(results) - keep]` is every result but the last `keep`, as long as there are more than `keep`.
