Keep the conversation you send in a new list, `list(messages)`, and add the reply and the problems to it after each attempt, so the caller's list stays as it was.

---

Check `finish_reason` before reading the text: a reply cut off at its limit isn't read at all. `json.loads` raises `json.JSONDecodeError`, and `str(error)` says where the JSON went wrong.

---

`"\n".join(["Your reply doesn't match the schema:", *(f"- {problem}" for problem in problems), "Reply again with only the corrected JSON."])` writes the message.
