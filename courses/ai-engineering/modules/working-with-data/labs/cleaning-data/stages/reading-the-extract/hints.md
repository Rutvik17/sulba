`read_csv` takes `na_values`, the strings to read as missing, and `keep_default_na`, whether to add its own list of spellings to them.

---

`table.isna()` is a table of `True` and `False`, and its `mean()` is the share of `True` in each column. Keep the shares over 0, then sort them with `sort_values(ascending=False)`.
