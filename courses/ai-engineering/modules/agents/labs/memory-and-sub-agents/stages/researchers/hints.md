Each call of `answer` builds its own `messages`, starting from the system prompt and the question, so that no question sees another's searches.

---

Send `"tools": [SEARCH]` while `round_ < self.rounds - 1`, and leave it out of the last request.

---

The model's message goes back with its `tool_calls`, and each result follows it as a `tool` message with the call's id, as in the desk's own loop.
