Read the file as text and split it at the lines holding only a comma, `"\n,\n"`. `pd.read_csv(io.StringIO(text))` reads a string as if it were a file.

---

By default `read_csv` reads `NULL` as missing, and `keep_default_na=False` keeps it. `.str.strip()` trims the spaces around each description.
