`CREATE TABLE IF NOT EXISTS daily_zones (...)` creates the table on the first run and leaves it on the next. `PRIMARY KEY (day, zone)` goes after the columns.

---

Count each zone's pickups and takings in one query and its drop-offs in another, then `FULL JOIN` the two, with `coalesce(..., 0)` for a zone missing from one side. `INSERT INTO daily_zones (...) SELECT ...` writes the result, and `.rowcount` on what `conn.execute` returns says how many rows it wrote.

---

`DELETE FROM daily_zones WHERE day = %s` and the `INSERT` belong in one transaction: `with conn.transaction():` on the lab's autocommit connection starts one, commits it when the block ends, and rolls it back if the block raises.
