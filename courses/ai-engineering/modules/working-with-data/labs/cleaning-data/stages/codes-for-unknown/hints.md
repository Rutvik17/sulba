`column.isin(codes)` is `True` where a value is one of the codes, and `column.mask(condition)` puts a missing value wherever the condition is `True`.

---

A column of type `int64` can't hold a missing value, so pandas turns it into `float64` when one appears. `column.astype("Int64")`, with a capital I, can hold one, and stays whole numbers.

---

`table.isna().mean()` gives each column's share missing, and `table.drop(columns=names)` leaves the table it's called on as it was.
