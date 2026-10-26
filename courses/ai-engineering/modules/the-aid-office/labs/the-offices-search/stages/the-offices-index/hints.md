`hashlib.sha256(text.encode()).hexdigest()` gives a text's SHA-256, the same for the same text every time. Read each id's digest from the table first, and embed only the passages the table lacks or whose digest differs.

---

In autocommit mode, each statement takes effect as it runs. `with conn.transaction():` makes the statements inside it one transaction, which psycopg commits as the block ends and rolls back if the block raises. Embed before the block, so that a failed request comes before any change.

---

`INSERT ... ON CONFLICT (id) DO UPDATE SET body = EXCLUDED.body, ...` adds a row or changes the one with its id, and `DELETE FROM passages WHERE NOT (id = ANY(%s))`, given the list of ids, removes the rest.
