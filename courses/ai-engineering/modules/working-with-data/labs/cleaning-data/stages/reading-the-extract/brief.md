Start `cleaning.py`. A network of US hospitals has sent an extract of its records: a row for each encounter, one hospital stay of a patient with diabetes. It holds {% $fig.encounters %} encounters of {% $fig.patients %} patients, in {% $fig.columns %} columns. Before anything is counted in it, it has to be read the way it was written.

The extract writes `?` where a value is missing. In `A1Cresult` and `max_glu_serum`, it writes `None` where a blood test wasn't done: a result in itself, not a gap. By default, pandas' `read_csv` reads a list of common spellings as missing, `None` among them, and `?` isn't one of them.

Write `read_encounters`, which reads the extract with each `?` as missing and no other value, and `missing_shares`, the share of each column's values that are missing.

```
read_encounters(path) -> a DataFrame of the extract
missing_shares(table) -> a Series of shares, indexed by column name
```

`missing_shares` lists only the columns with a missing value, from the most missing to the least. The tests read `data/encounters.csv`.
