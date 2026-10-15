A contract turns what the documentation promises into rules the code checks, and each broken rule names its column and how many rows break it, so a failed extract says where to look:

```python
for column in COLUMNS:
    if column not in table:
        problems.append((column, "absent", len(table)))
        continue
    values = table[column]
    present = values.notna()
    if column not in MAY_BE_MISSING and not present.all():
        problems.append((column, "missing", int((~present).sum())))
    if column in ALLOWED:
        rows = int((present & ~values.isin(ALLOWED[column])).sum())
        if rows:
            problems.append((column, "not allowed", rows))
    if column in RANGES:
        low, high = RANGES[column]
        numbers = pd.to_numeric(values, errors="coerce")
        inside = numbers >= low if high is None else numbers.between(low, high)
        rows = int((present & ~inside).sum())
        if rows:
            problems.append((column, "out of range", rows))
```

`isin` and `between` are `False` for a missing value, so without `present` each missing value would also count as a wrong one. `pd.to_numeric(..., errors="coerce")` makes a value that isn't a number missing before the range is compared, so text in a column of numbers counts as out of range, where comparing it would stop the check with an error.

The contract holds the extract's spellings, not the documentation's. The documentation writes gender as male and female, age groups as `[0, 10)` and the label for no readmission as `No`; the extract writes `Male`, `[0-10)` and `NO`. With the documentation's spellings, the contract would fail {% $fig.gender_failing %} encounters on gender, {% $fig.age_failing %} on age, and the {% $fig.no_failing %} labelled `NO`. Write a contract from the documentation, run it on an extract you know to be good, and correct the contract wherever it fails there.
