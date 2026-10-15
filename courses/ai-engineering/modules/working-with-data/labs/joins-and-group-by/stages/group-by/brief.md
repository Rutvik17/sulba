Now count. Write `readmission_rates`, which groups a table's encounters by the values of the column `by` and gives each value's encounters, those readmitted within {% $fig.days %} days and their share, from the highest share to the lowest. A missing value is a group of its own, and values with fewer than `smallest` encounters are left out, such as those with fewer than {% $fig.smallest %}.

```
readmission_rates(table, by, smallest) -> a DataFrame of encounters, readmitted and share, by value
```

The tests group each patient's first encounter, without deaths and hospice care: {% $fig.patients %} patients.
