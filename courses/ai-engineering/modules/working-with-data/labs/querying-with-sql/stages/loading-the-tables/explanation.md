`to_sql` writes a DataFrame as a table: each column takes a type from its pandas type, such as `INTEGER` or `TEXT`, and each missing value becomes `NULL`. The {% $fig.no_specialty %} encounters with no medical specialty hold `NULL` there.

```python
connection.executemany("INSERT INTO codes VALUES (?, ?, ?)", rows)
connection.commit()
```

Each `?` in the statement is a placeholder: `executemany` hands the database each row's values to put in their place, as values, so a description is stored as written, quotes and all. Written into the SQL itself, as `f"... '{description}'"`, a quote ends the text early, and text from outside the code could add SQL of its own. This `?` has nothing to do with the `?` the extract writes for a missing value.

The primary key makes the database refuse a second row for the same `(column_name, code)`, as `validate="many_to_one"` refused a code listed twice in pandas. An `INSERT` opens a transaction that only `commit` saves: close the connection before it, and the codes are gone. `to_sql` commits its own rows.
