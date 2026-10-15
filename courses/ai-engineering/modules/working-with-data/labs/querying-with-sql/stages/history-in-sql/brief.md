The data scientists want each encounter's history from the database too, as in Joins and group-by: for each encounter, from the same patient's encounters with a lower `encounter_id`, how many there were, `earlier_encounters`; how many of them were followed by a readmission within {% $fig.days %} days, `earlier_readmissions`; and the description of the last one's discharge, `previous_discharge`. Write `history`, which asks the database for them.

```
history(connection) -> a DataFrame of encounter_id and the three columns, in order of encounter_id
```

A first encounter has no earlier encounters or readmissions, and no previous discharge. SQL's window functions compute over each patient's rows in turn, without grouping them into one: `COUNT(*) OVER (PARTITION BY patient_nbr ORDER BY encounter_id)` counts each patient's rows up to and including the current one, and `LAG(x) OVER (...)` gives `x` from the row before.

The tests load each database with your `load`, some holding only the columns `history` needs: `encounter_id`, `patient_nbr`, `discharge_disposition_id` and `readmitted`.
