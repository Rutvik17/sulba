In `noted`, put the `yield` in a `try` clause. An `except` clause around it gets the block's error, adds the note and raises it again.

---

`Batch.__enter__` returns the batch itself, so `with Batch(struct) as batch:` gives the block the batch.

---

`__exit__` gets `None` for `error` when the block raised nothing. Raise the group then, if any line failed, and return `False` either way, so an error of the block's own goes on.
