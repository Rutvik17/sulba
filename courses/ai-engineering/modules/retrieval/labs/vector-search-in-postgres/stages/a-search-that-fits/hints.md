`CREATE INDEX ... USING hnsw ((subvector(embedding, 1, 256)::halfvec(256)) halfvec_cosine_ops)` indexes each vector's first 256 numbers at half precision. A query goes through it only when it orders by that same expression: `ORDER BY subvector(embedding, 1, 256)::halfvec(256) <=> subvector(%(vector)s::vector, 1, 256)::halfvec(256)`.

---

`SELECT id FROM (SELECT id, embedding FROM passages ORDER BY ... LIMIT 40) AS candidates ORDER BY embedding <=> %(vector)s LIMIT %(k)s` takes the index's 40 nearest candidates, then sorts them by the full vectors.

---

`INSERT ... ON CONFLICT (id) DO UPDATE SET body = EXCLUDED.body, ...` changes the row that's there to the values the insert brought, and `cursor.executemany(query, rows)` runs it for each row.
