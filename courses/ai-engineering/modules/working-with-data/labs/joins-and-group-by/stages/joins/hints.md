Rename each mapping table's columns to the code column's name and the description's, then `table.merge(names, on=column, how="left", validate="many_to_one")`.

---

`merge(..., indicator=True)` adds a column `_merge`, which is `"left_only"` for a row of the table the mapping had no row for.
