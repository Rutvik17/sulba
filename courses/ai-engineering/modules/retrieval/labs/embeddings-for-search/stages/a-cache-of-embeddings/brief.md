A vector comes from the model, the prefix and the text, so a text the help desk has embedded needn't be embedded again: when a page changes, only its changed passages need new vectors. And {% $fig.repeated %} of its {% $fig.passages %} passages have the same text as another, from pages that share a section, so it needs only {% $fig.distinct %} vectors for them all.

In `cache.py`, write `key(prefix, text)`, the text's key: the sha256 of the model's name, a newline, the prefix and the text, in UTF-8, as 64 hexadecimal digits.

Then `Cache(path)`, which keeps vectors in an SQLite database in the file at `path`, through Python's `sqlite3`, in this table:

```sql
CREATE TABLE IF NOT EXISTS vectors (key TEXT PRIMARY KEY, vector BLOB NOT NULL)
```

Each row holds a text's key and its vector's bytes: `vector.tobytes()` of a float32 vector, which `np.frombuffer(blob, dtype=np.float32)` reads back.

`cache.vectors(client, texts, prefix, batch)` returns each text's vector, as `embed` does. It takes the vectors the file has, and embeds the rest with your `embed`: each text once, however many times it comes in `texts`, in order, at most `batch` to a request. Keep each batch's vectors in the file as soon as they come, so that when a request fails, the batches before it stay kept, and the next call embeds only the rest.

```
key(prefix, text) -> str
Cache(path).vectors(client, texts, prefix, batch=BATCH) -> np.ndarray
```

`Cache` closes its file with `close()`, or at the end of a `with` block.
