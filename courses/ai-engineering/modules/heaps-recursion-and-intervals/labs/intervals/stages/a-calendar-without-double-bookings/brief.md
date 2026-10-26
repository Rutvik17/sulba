Write `Calendar`:

```
Calendar() -> a calendar with no bookings
calendar.book(start, end) -> True, adding the booking, or False if it overlaps one, adding
    nothing
```

A booking runs from its start up to its end, with `start < end`, so one that ends at 20 and one that starts at 20 don't overlap. With `calendar = Calendar()`, `calendar.book(10, 20)` returns `True`, `calendar.book(15, 25)` returns `False`, and `calendar.book(20, 30)` returns `True`. The tests' longest run makes {% $fig.bookings %} bookings.
