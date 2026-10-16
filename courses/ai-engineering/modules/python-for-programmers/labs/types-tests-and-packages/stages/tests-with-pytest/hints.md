Test one behaviour at a time, over several values with `parametrize`: numbers that pass, and `True`, `False`, `math.nan`, `"17.99"` and `None`, which don't.

---

An array that checked only its first item would pass `[17.99, "3"]`, and one that took any sequence would pass `(17.99, 3)`. Test both.

---

Check the message with `str(raised.value) == "..."`, backticks and all, and that the error is a `TypeError`.
