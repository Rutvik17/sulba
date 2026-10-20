`ALTER TABLE passages ADD COLUMN words tsvector GENERATED ALWAYS AS (...) STORED` adds the column and fills it for every passage already in the table. `CREATE INDEX ... ON passages USING gin (words)` indexes it.

---

`words @@ query` is true when a passage's words match the query. Put the query in the `FROM` clause, as in `FROM passages, websearch_to_tsquery('english', %(question)s) AS query`, and it's worked out once and named for the rest of the statement. Sort by `ts_rank_cd(words, query) DESC, id`, then `LIMIT`.

---

`replace(plainto_tsquery('english', %(question)s)::text, '&', '|')::tsquery` gives the query of any word. Postgres doesn't take a cast of a function's result in `FROM`: work it out in a `WITH` clause and join it as you would a table.
