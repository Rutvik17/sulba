Script the model to fail with `model.fails(503, "Loading model")`, and read what a customer would see.

---

`model.says("Our prices", finish_reason="length")` scripts a reply cut off at its limit. Which check in `answer` lets it through?

---

Print `model.requests[1].body["messages"]` after two questions, and read each message's role.

---

A request's prompt and its reply share the window. Count the tokens of each request a long conversation sends, and add `REPLY`.
