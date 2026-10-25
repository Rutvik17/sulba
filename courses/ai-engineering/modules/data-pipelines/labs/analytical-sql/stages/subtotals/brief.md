The company's accountants want each day's trips and takings, the `total` each rider paid, by borough and by the way riders paid, with each borough's subtotal and the day's total. On 5 August, {% $fig.trips %} trips took ${% $fig.takings %}, paid in {% $fig.payments %} ways; {% $fig.flex %} were Flex Fare trips, booked at a price set before the ride.

In `payments.py`, write `by_payment(conn, day)`, a row for each borough and payment, each borough's subtotal and the day's total, of the trips picked up on `day`. Each row has its `level`, `"payment"`, `"borough"` or `"all"`; its pickup `borough`; its payment's `name` from `payments`; its `trips`; and its `revenue`, the sum of their `total`.

- A subtotal's `payment` is `None`, and the day's total has `None` for both `borough` and `payment`.
- Trips from a zone with no borough are a borough of their own, `None`, with its own payments and subtotal.
- Boroughs come in alphabetical order, the one with no name last, each with its payments in order of their code and then its subtotal. The day's total comes last.
- `trips` is an `int`, and `revenue` a `Decimal`, exact to the cent.

```
by_payment(conn, day) -> list of (level, borough, payment, trips, revenue)
```
