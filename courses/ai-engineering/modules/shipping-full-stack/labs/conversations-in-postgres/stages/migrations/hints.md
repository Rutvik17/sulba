`REFERENCES conversations ON DELETE CASCADE` makes a column refer to a conversation and go with it, `CHECK (outcome IN (...))` holds a column to its values, and `PRIMARY KEY (conversation_id, position)` allows one message at each position.

---

`with conn.transaction():` on an autocommit connection runs its block as one transaction: committed when the block ends, and rolled back if it raises. A migration's SQL can hold more than one statement, since `conn.execute(sql)` runs them all when it's given no parameters.

---

`SELECT pg_advisory_lock(%s)` waits for the lock and holds it for the session, through every transaction after it, and `SELECT pg_advisory_unlock(%s)` releases it. A `try` and `finally` releases it however `migrate` ends.
