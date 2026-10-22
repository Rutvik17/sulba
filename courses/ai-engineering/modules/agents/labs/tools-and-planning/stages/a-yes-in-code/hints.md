`heard` gives `None` both when nothing was pending and when the message dropped a proposal: either way the model reads the message as it came.

---

The model's message goes back as it came, with its `tool_calls` when it called tools, and each tool's result follows in a message with the role `tool` and the call's id.
