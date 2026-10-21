`time.perf_counter()` before and after the request gives the seconds it took.

---

The model's message goes back as it came, with its `content` and, when it called tools, its `tool_calls`, before the tools' results. Its final reply goes in `messages` too, so that the caller's next message follows it.

---

`for _ in range(self.rounds):` with `raise OutOfRounds(...)` after the loop ends a turn that never got a reply.
