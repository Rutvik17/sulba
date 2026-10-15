Read as one table, the file comes out as {% $fig.naive_rows %} rows under the first table's header: the other tables' headers become rows, each separator line a row of missing values, and every `NULL` a missing value. Split into its tables first, each section is a small CSV of its own:

```python
with open(path) as file:
    sections = file.read().strip().split("\n,\n")
```

`io.StringIO` makes a string act as a file, so `read_csv` reads each section, and its first column's name says which code column the table describes. `keep_default_na=False` keeps the {% $fig.nulls %} descriptions written `NULL` as text. The codes they describe stand for unknown, and a missing description would look like a code the mapping lacks. `.str.strip()` trims the spaces around each description, without which `" Physician Referral"` and `"Physician Referral"` would be different values.
