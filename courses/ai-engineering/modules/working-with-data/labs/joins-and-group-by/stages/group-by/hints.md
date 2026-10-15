`table["readmitted"] == "<30"` is `True` for each readmission that counts. Group it by `table[by]` with `dropna=False`.

---

`.agg(encounters="size", readmitted="sum")` gives each group's count of rows and of `True` values, as columns named for them.
