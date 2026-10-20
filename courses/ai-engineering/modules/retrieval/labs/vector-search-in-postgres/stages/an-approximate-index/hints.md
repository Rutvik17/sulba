`CREATE INDEX passages_embedding ON passages USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64)` builds the index with the defaults. `sql.SQL("... WITH (m = {}, ef_construction = {})").format(sql.Literal(m), sql.Literal(ef_construction))`, from `psycopg.sql`, puts the values into the statement.

---

`with conn.transaction():` runs its block in one transaction, even in autocommit mode. In it, `conn.execute("SELECT set_config('hnsw.ef_search', %s, true)", (str(ef_search),))` sets the list's size until the block ends; `set_config` takes the value as text.

---

`conn.execute("EXPLAIN (FORMAT JSON) SELECT ...", (vector, k)).fetchone()[0]` is the plan: a list with one object, whose `"Plan"` is its top node. The index scan can be a node under it, in `"Plans"`, so look through every node for `"Index Name"`.
