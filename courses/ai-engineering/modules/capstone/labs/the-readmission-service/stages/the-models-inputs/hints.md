Build the result column by column on `pd.DataFrame(index=rows.index)`, so each input lines up with its row.

---

`rows["age"].str.extract(r"\[(\d+)-(\d+)\)")` gives each band's two ends as text columns `0` and `1`; `.astype(int)` makes them numbers.

---

`.astype(str)` turns a column of codes into text, and leaves a column that's already text as it is.
