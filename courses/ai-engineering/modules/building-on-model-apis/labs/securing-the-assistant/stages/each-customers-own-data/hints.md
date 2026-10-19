`db.execute(sql, (value, ...))` puts each value where the SQL has a `?`, as a value SQLite never reads as SQL. Every query of bookings asks for `customer = ?`, with `self.customer`.

---

`booking` asks for `reference = ? AND customer = ?`, so another customer's booking finds no row, as a missing one does.

---

`PARAMETERS` gives each tool's parameters. Check that the arguments are a `dict` whose keys, sorted, are those, and whose values are each a `str`, before calling the method.
