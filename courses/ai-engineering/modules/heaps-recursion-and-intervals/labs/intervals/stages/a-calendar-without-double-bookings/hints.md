Keep the bookings sorted by start. Which bookings can a new one overlap?

---

`bisect.bisect_right` finds where the new start goes among the sorted starts. Only the booking before that place and the one at it can overlap: check that the one before ends by the new start, and the one at it starts no earlier than the new end.
