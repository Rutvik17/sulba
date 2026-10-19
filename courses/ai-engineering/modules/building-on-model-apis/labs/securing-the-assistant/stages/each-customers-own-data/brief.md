The shop's assistant now answers customers who have signed in, about their own bookings. The model chooses which tool to call and what to pass it, and what it chooses follows from what it reads: the customer's message, and whatever earlier calls returned, such as a review someone else wrote. So any customer can try to talk it into any call. Each tool has to be safe whatever the model asks of it.

The shop keeps its data in SQLite, in the two tables of `SCHEMA` in `shop.py`:

- `bookings`: each booking's `reference`, `customer`, `day`, `time`, `service`, `bike`, `notes` and `status`;
- `reviews`: each review's `id`, the `part` it's about, its `author`, its `stars` and its `text`.

In `shop.py`, write `Tools(db, customer)`, the tools for the customer the shop's sign-in names:

- `my_bookings()`: the customer's bookings, soonest first, each its `reference`, `day`, `time`, `service` and `status`;
- `booking(reference)`: one of the customer's bookings, with its `bike` and `notes` too. When the customer has no booking with that reference, whether or not another customer has, raise `ToolError(f"There's no booking {reference}.")`;
- `reviews(part)`: a part's reviews, oldest first, each its `stars` and `text`, and never who wrote it;
- `run(call)`: the content of the tool message that answers a call from the model's reply. That's the tool's value as JSON, written with `ensure_ascii=False`, or `{"error": ...}` when the call can't run: a tool `TOOLS` doesn't list, arguments that aren't a JSON object of exactly the tool's parameters, each a string, or a `ToolError`. It never raises.

Pass every value to SQLite as a parameter, `?`, and never as part of the SQL.

```
Tools(db, customer).run(call) -> str
```
