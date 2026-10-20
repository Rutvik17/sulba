An exact search works out the distance to every passage, so its time grows with the table. pgvector's HNSW index keeps the vectors in a graph instead, each linked to some of its nearest, and a search follows the links toward the question, reading only part of the table. It can miss a passage the exact search finds: unlike an index on a column of text, an approximate index can change a query's results.

In `index.py`, write:

- `build(conn, m, ef_construction)`: an HNSW index named `passages_embedding` on the passages' `embedding`, for cosine distance, with `m` and `ef_construction` as its options.
- `search(conn, vector, k, ef_search)`: the ids of the `k` passages nearest to `vector` by cosine distance, nearest first, with a candidate list of `ef_search` for this search alone. Set `hnsw.ef_search` with `set_config` in a transaction around the query, so that the setting ends with it.
- `uses_index(conn, vector, k)`: whether the plan Postgres makes for that query, without running it, goes through the index, from `EXPLAIN (FORMAT JSON)`.

```
build(conn, m=16, ef_construction=64)
search(conn, vector, k=10, ef_search=40) -> list of ids
uses_index(conn, vector, k=10) -> bool
```
