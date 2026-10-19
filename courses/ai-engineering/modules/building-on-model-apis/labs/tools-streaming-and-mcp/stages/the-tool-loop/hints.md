Keep the conversation you send in a new list. After a reply with tool calls, add the model's message as it came, its `role`, `content` and `tool_calls`, and then a tool message for each call.

---

`{function.__name__: function for function in functions}` finds a call's function by its name, and `run` turns the call into its tool message.

---

Count requests, not calls: a round is one request, however many calls its reply makes.
