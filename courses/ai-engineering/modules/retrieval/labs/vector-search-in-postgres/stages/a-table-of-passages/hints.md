`STORAGE PLAIN` goes after a column's type in `CREATE TABLE`, before its constraints: `embedding vector(768) STORAGE PLAIN NOT NULL`.

---

`conn.cursor().copy("COPY passages (...) FROM STDIN WITH (FORMAT BINARY)")` gives a writer for the rows, in a `with` block. In the binary format Postgres applies no casts, so each value has to arrive as its column's exact type: tell the writer the columns' types first, with `copy.set_types(["text", ..., "vector"])`, then `copy.write_row(row)` for each row. Once the `with` block has ended, the rows are in the table for `ANALYZE passages` to read.

---

`conn.execute(query, (vector, k))` fills the query's `%s` placeholders in order. `ORDER BY embedding <=> %s LIMIT %s` sorts the rows by their distance to the vector and keeps the first `k`.
