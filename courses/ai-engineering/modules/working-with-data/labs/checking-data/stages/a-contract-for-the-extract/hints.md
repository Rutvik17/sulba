For each column of `COLUMNS`: `column not in table` finds an absent one, and `values.notna()` marks the values present. Count `missing` only in a column outside `MAY_BE_MISSING`.

---

`values.isin(allowed)` is `False` for a missing value, and so is `values.between(low, high)`: count the values that are present and outside, `(present & ~values.isin(allowed)).sum()`. `pd.to_numeric(values, errors="coerce")` turns a value that isn't a number into a missing one, before the range is compared.
