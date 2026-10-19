The shop wants every email that asks for a repair booked straight into its calendar, and every other email left for a person to answer. This stage writes the code that does it, from the email to the booking, with your `ask_for` and `errors`.

In `inbox.py`, write `book(client, email, today)`. It asks the model, with `INSTRUCTIONS` and the email, for a reply held to a form you write, which is one of:

```json
{"booking": null}
{"booking": {"name": "Ana Silva", "bike": "city", "service": "brakes", "date": "2026-10-24", "time": "10:30", "bikes": 1, "phone": null, "notes": ""}}
```

`null` says the email asks for no booking. A booking has every one of these keys, and no other:

- `name`, the customer's name, and `notes`, anything else the email says about the repair;
- `bike`, one of `BIKES`, and `service`, one of `SERVICES`;
- `date`, as `YYYY-MM-DD`, and `time`, as `HH:MM`;
- `bikes`, how many bikes, from `1` to `3`;
- `phone`, a number, or `null` when the email gives none.

The shop opens Monday to Friday for bookings starting on the hour or the half hour from `09:00` to `16:30`, and on Saturday from `09:00` to `12:30`. It's closed on Sunday, and it books from tomorrow to `today + AHEAD`.

Return a `Booking`, with the date as a `date`. Raise `NotBooked` when the email asks for no booking, when no reply fits the form, and when the shop can't take the booking it asks for. Let a `ModelError` through, so the email can be tried again later.

```
book(client, email, today) -> Booking
```

Two tests run on every attempt. Then six checks run before the code ships.
