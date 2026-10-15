The network's dashboards ask their questions in SQL, of a database that holds the extract. Python's `sqlite3` keeps a database in a file, or in memory with `sqlite3.connect(":memory:")`, and a connection runs SQL on it. Start `queries.py`. Write `load`, which puts the encounters and the mapping into a database:

- a table `encounters`, of the extract's {% $fig.columns %} columns, each missing value `NULL`;
- a table `codes` of `column_name`, `code` and `description`, a row for each code of each code column, with `(column_name, code)` its primary key, so that the database refuses a code listed twice.

```
load(connection, table, mapping) -> None
```

`table` is the extract as pandas reads it, with `?` missing. `mapping` holds the mapping's tables by the column each describes, each a DataFrame of `code` and `description`. What `load` puts in the database stays there once the connection closes.
