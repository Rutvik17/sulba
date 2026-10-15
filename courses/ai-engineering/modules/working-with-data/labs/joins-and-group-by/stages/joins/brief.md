Now give each encounter its descriptions. Write `describe`, a copy of the table with a description column beside each code column: `admission_type`, `discharge_disposition` and `admission_source`. Every encounter stays, once, in its order. A code the mapping lacks gets a missing description, and a mapping that lists a code twice raises an error rather than doubling the encounters.

Then write `unmatched`, which finds the codes a table holds that the mapping lacks, for each code column, so that a new code is noticed before it's counted as unknown.

```
describe(table, mapping) -> a DataFrame, the table with its descriptions
unmatched(table, mapping) -> a dict of sorted lists of codes, by column
```

The tests read `data/encounters.csv` with `?` as missing, and the mapping with your `read_mapping`.
