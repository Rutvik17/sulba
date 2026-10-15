The documentation calls `encounter_id` the unique identifier of an encounter, and every report joins the mapping's descriptions to the codes. Write `key_problems`, which checks both, as `(column, problem, rows)`:

- `encounter_id` `repeated`: every row whose id another row has too;
- then, for each column the mapping describes, in the mapping's order: `repeated in the mapping`, every row of the mapping whose code another row lists too, and `not in the mapping`, every row of the table whose code the mapping lacks.

```
key_problems(table, mapping) -> a list of (column, problem, rows), empty when the keys and codes hold
```

`mapping` holds the mapping's tables by the column each describes, each a DataFrame of `code` and `description`, as the tests read them from `data/ids-mapping.csv`.
