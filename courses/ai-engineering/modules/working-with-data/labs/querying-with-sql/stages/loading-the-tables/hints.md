`table.to_sql("encounters", connection, index=False)` writes a DataFrame as a table. The other table takes SQL of its own:

```sql
CREATE TABLE codes (column_name TEXT, code INTEGER, description TEXT, PRIMARY KEY (column_name, code))
```

---

`connection.executemany("INSERT INTO codes VALUES (?, ?, ?)", rows)` inserts each row's values in place of the `?`s. Then `connection.commit()`: an insert waits in a transaction until it's committed.
