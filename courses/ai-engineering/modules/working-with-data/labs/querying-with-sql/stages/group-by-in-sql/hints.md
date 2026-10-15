`readmitted = '<30'` is true or false for each encounter, which SQLite keeps as a number, so `SUM` of it counts the readmissions and `AVG` gives their share. `HAVING COUNT(*) >= ?` filters the groups once they're counted.

---

`PRAGMA table_info(encounters)` gives a row for each of the table's columns, its name second. `pd.read_sql_query(query, connection, params=(smallest,))` passes `smallest` for the `?`.
