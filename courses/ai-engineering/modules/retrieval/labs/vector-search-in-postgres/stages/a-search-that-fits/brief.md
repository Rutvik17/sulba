The help desk's database will run on a small server, with room in memory for {% $fig.budget %} of the search's indexes, {% $fig.budget_bytes %} bytes, beside the rest, and an index of the full vectors, as your `index.py` builds, doesn't fit. This stage builds the search it will ship, in `desk.py`, on the table your `store.py` makes and loads:

- `build(conn)` makes the indexes the search goes through, once the passages are loaded.
- `search(conn, vector, k, domain)` gives the ids of the `k` passages nearest to `vector` by the full vectors' cosine distance, nearest first, through an index `build` made; with `domain`, the `k` nearest of that service's passages.
- `update(conn, rows)` puts each row, a passage's id, domain, page, body and vector as `load` takes them, into the table: a passage that isn't there yet is added, and one that is takes the row's place.

How the indexes keep each vector is yours to choose. The checks use the {% $fig.test %} test questions: of each one's {% $fig.k %} nearest passages by the full vectors, `search` must find {% $fig.kept %} on average.

```
build(conn)
search(conn, vector, k=10, domain=None) -> list of ids
update(conn, rows)
```

Two tests run on every attempt. Then five checks run before the code ships.
