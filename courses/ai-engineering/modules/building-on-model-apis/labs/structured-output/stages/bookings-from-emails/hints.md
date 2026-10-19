The form's `booking` is an object or `null`: `"type": ["object", "null"]`, with its `properties`, `required` and `"additionalProperties": false` beside it. An `enum` can list every time a booking can start.

---

What the form can't hold, the code checks once the reply fits it: `date.fromisoformat` for a date that exists, `day.weekday()` for the day of the week, and Saturday's earlier close.

---

A JSON Schema `integer` can arrive as `2.0`, so `int(...)` the bikes. `except NoMatch` turns the model's last failed reply into `NotBooked`, and leaves `ModelError` alone.
