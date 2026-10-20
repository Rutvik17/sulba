`conn.execute("EXPLAIN " + query, params).fetchall()` shows the plan Postgres makes for a query. Is the index's name in the plan for `search`'s query?

---

What text does Postgres get from `search_in(conn, vector, "va' OR 'x' = 'x")`?

---

`EXPLAIN` the query `search_in` runs, with `hnsw.iterative_scan` set: is there a sort above the CTE?

---

`<#>` gives the inner product times -1. Which passage has the largest value of it?
