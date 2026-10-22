`self.desk.callbacks` holds each booked call as a dictionary of its ticket, day and time, and each ticket's service is in `self.desk.tickets`.

---

`confirm` can tell a move from any other proposal with `isinstance(self.pending, Move)`, and leave the rest to `super().confirm()`.

---

Booking the new time first means a booking that fails leaves the old call where it was.
