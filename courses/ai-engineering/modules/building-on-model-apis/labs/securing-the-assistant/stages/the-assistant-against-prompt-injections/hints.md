Keep the conversation in `self.messages`: the system message, then each message of the customer's, each assistant message as it came, each tool result, and the model's answer as the assistant's.

---

Put `try` and `except httpx.HTTPError` around each request, and `except sqlite3.Error` around each tool call, with a result that names no table or column.

---

Keep each day's tokens in a table by customer and day, and check them before every request, not only before each message.
