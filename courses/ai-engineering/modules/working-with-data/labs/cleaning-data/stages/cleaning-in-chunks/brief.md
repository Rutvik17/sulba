The network's full extract holds millions of encounters, more than fits in memory at once. `read_csv` can read a file in chunks: with `chunksize`, it gives the rows as DataFrames of that many rows, one after another, each read only when it's asked for.

Write `clean_chunks`, which takes those chunks and gives the table your functions give for the whole extract, holding one chunk at a time: the codes for unknown marked, each patient's first encounter, and no deaths or hospice care.

```
clean_chunks(chunks) -> a DataFrame, one row per patient left in
```

A patient's encounters can come in any chunk, in any order. The tests read `data/encounters.csv` in chunks of {% $fig.chunk %} rows, and in one chunk, giving `read_csv` each column's type, `types`, as the whole extract reads:

```python
pd.read_csv(path, na_values=["?"], keep_default_na=False, dtype=types, chunksize=1000)
```
