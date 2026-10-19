Customers can now cancel a booking through the assistant. But anything the model reads can talk it into a call, so the tool the model calls to cancel can't cancel anything itself. It proposes, and the customer confirms, with a button the chat window shows under the reply. The model never sees the button or what it sends back.

In `actions.py`, write `Actions(db)`:

- `propose_cancel(customer, reference, now)`: when the customer has a booking with that reference whose `status` is `booked`, a `Pending` action with a new `id` from `secrets.token_urlsafe(16)`, the customer, the reference, the question its button asks, such as `Cancel booking B-1042, brakes on 2026-10-24 at 10:30?`, and the time it expires, `WAIT` after `now`. Keep it for its customer to confirm. Otherwise raise `Refused(f"There's no booking {reference} to cancel.")`.
- `confirm(customer, id, now)`: take the action with that id, setting its booking's `status` to `cancelled`, and return `f"Booking {reference} is cancelled."`. An action is taken once, by its own customer, before it expires. Raise `Refused("That action isn't waiting for you.")` for an id no action of the customer's has, `Refused("That action has expired.")` after it expires, and `Refused(f"Booking {reference} can't be cancelled now.")` when the booking is no longer `booked`. Another customer's attempt leaves the action waiting for its own.

```
Actions(db).propose_cancel(customer, reference, now) -> Pending
Actions(db).confirm(customer, id, now) -> str
```
