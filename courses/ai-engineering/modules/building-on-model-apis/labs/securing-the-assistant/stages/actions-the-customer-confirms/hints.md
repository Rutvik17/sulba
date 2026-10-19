Keep each `Pending` in a `dict` by its id. Look the id up and check its customer before anything else, and remove the action once it's taken or has expired.

---

`secrets.token_urlsafe(16)` gives 22 characters from 16 random bytes. An id made from the reference, or from a count of actions, could be guessed.

---

Cancel with `UPDATE ... WHERE reference = ? AND customer = ? AND status = 'booked'`, and read the cursor's `rowcount`: `0` means the booking changed after it was proposed.
