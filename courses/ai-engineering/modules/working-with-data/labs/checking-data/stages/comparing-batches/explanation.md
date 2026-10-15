`value_counts(dropna=False)` counts a missing value as a value of its own, and dividing by the batch's rows turns the counts into shares, which compare across batches of any size. `pd.concat(..., axis=1)` lines the two batches' shares up by value, keeping a value either one holds, and `fillna(0)` gives a value one batch lacks no share there.

```python
for column in WATCHED:
    before = previous[column].value_counts(dropna=False) / len(previous)
    after = current[column].value_counts(dropna=False) / len(current)
    both = pd.concat({"previous": before, "current": after}, axis=1).fillna(0)
    both["change"] = both["current"] - both["previous"]
    moved = both[both["change"].abs() > tolerance]
    found.append(moved.rename_axis("value").reset_index().assign(column=column))
```

Without `dropna=False`, `value_counts` leaves missing values out, so a column going missing in many rows never reports the missing value's share.

A change isn't always a fault. Split by `encounter_id`, the extract's first {% $fig.half %} encounters and the rest differ: admission source {% $fig.code %}, which the mapping calls `NULL`, falls from {% $fig.earlier_share %} of the earlier encounters to {% $fig.later_share %} of the later ones. The comparison can't say why: a change in how the hospitals recorded admission sources looks the same as a change in their patients. It says what moved, so that someone looks before a model built on one kind of encounter is used on the other.
