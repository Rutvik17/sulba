```python
repeated = int(table["encounter_id"].duplicated(keep=False).sum())
if repeated:
    problems.append(("encounter_id", "repeated", repeated))
for column, codes in mapping.items():
    twice = int(codes["code"].duplicated(keep=False).sum())
    if twice:
        problems.append((column, "repeated in the mapping", twice))
    values = table[column]
    lacking = int((values.notna() & ~values.isin(codes["code"])).sum())
    if lacking:
        problems.append((column, "not in the mapping", lacking))
```

`duplicated` marks the second and later rows of a value; with `keep=False` it marks every one of them, so the count says how many rows are tangled up in the repeat. An id two encounters share would match each of them in every join on it, and a code the mapping lists twice would double each encounter it describes. The mapping is data too, and a contract checks it as it checks the extract.

A code the mapping lacks isn't wrong in itself: it may be a new code the mapping hasn't caught up with. The check can't tell which, but it can say how many rows wait on the answer, so that no report counts them as unknown without anyone deciding to.
