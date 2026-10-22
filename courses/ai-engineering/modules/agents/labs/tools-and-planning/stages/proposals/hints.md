A time is in the morning when it comes before `"12:00"`. The free times are in the order of the day, so the first that fits is the earliest.

---

`self.desk.open_ticket(service, summary)` gives the new ticket's id, for `book_callback` to book on.

---

Check the time is still in `self.desk.free[service][day]` before opening anything, so a callback that can't be booked doesn't leave a new ticket behind.
