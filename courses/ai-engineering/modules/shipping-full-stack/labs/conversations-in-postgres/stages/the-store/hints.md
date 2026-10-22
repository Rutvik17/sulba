`with self.pool.connection() as conn:` lends a connection from the pool and gives it back when the block ends. `with self.pool.connection() as conn, conn.transaction():` makes the block one transaction too.

---

`SELECT 1 FROM conversations WHERE id = %s FOR UPDATE` locks the conversation's row until the transaction ends, so a second turn's transaction waits there until the first has committed. Count the messages once the lock is taken.

---

`cursor.executemany(sql, rows)`, on `conn.cursor()`, runs the statement once for each row of parameters.
