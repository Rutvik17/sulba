`SELECT set_config('hnsw.iterative_scan', 'relaxed_order', true)`, in the same transaction as `hnsw.ef_search`, turns iterative scans on until it ends.

---

`WITH found AS MATERIALIZED (SELECT id, embedding <=> %s AS distance FROM passages WHERE ... ORDER BY distance LIMIT %s) SELECT id FROM found ORDER BY ...` finds the rows in the CTE first, then sorts them.

---

`SELECT DISTINCT domain FROM passages ORDER BY domain` gives each service once.
