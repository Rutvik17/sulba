The network's data scientists are building a model that flags, at discharge, the patients likely to be readmitted within {% $fig.days %} days. Alongside each encounter's own columns, they want the patient's history before it. Write `history`, which gives each encounter of a table three columns, from the same patient's encounters with a lower `encounter_id`:

- `earlier_encounters`: how many there were;
- `earlier_readmissions`: how many of them were followed by a readmission within {% $fig.days %} days;
- `previous_discharge`: the description of the last one's discharge, from the mapping.

```
history(table, mapping) -> a DataFrame of the three columns, a row for each encounter
```

A patient's first encounter has no earlier encounters or readmissions, and no previous discharge. Nothing comes from the encounter's own outcome or from later encounters: neither is known at discharge. `groupby` can work down each group in order, with methods such as `cumcount`, `cumsum` and `shift`.

The tests read `data/encounters.csv` with `?` as missing, and the mapping with your `read_mapping`.
