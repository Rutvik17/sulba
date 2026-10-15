Now describe each encounter in SQL. Write `describe`, which asks the database for each encounter's `encounter_id` and the descriptions of its codes, as `admission_type`, `discharge_disposition` and `admission_source`, from the table `codes`. Every encounter comes once, in order of `encounter_id`, and an encounter whose code the table lacks keeps its row, the description missing.

```
describe(connection) -> a DataFrame of encounter_id and the three descriptions
```

`pd.read_sql_query(query, connection)` runs a query and gives its rows as a DataFrame. The tests load the database with your `load`.
