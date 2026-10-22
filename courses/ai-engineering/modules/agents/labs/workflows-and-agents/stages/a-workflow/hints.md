`chat(client, messages, response_format={"type": "json_schema", "json_schema": {"schema": ROUTE}})` asks for a reply that follows the schema, and `json.loads` reads it.

---

Keep the offer as an action and its arguments, such as `("book", {"ticket": "T-2101", "day": "2026-11-03", "time": "14:00"})`, and take it off the workflow at the start of each reply, so that only the next message can say yes to it.

---

A time is in the morning when it comes before `"12:00"`: times on the hour compare as text in the order of the day.
