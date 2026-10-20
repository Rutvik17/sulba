The help desk's search finds passages by their vectors. Postgres can find them by their words too, with its full-text search: it reads each passage into words, each cut to its stem and the commonest left out, and finds the passages that hold a question's words. This lab compares the two ways of searching, puts them together, and has a second model put what they find in order. `uv run sulba.py db` starts the lab's database on your machine, and each test gets a new, empty one. `load`, already written, puts the help desk's passages in the table `passages`, each with its `id` and its text in `body`.

In `fts.py`, write:

- `index(conn)`: a column `words` of the table, generated from each passage's `body` by `to_tsvector('english', body)` and stored, and a GIN index on it.
- `every_word(conn, question, k)`: the ids of the `k` passages that hold every word of `question`, as `websearch_to_tsquery('english', question)` reads it, best first by `ts_rank_cd`, a tie going to the id that sorts first.
- `any_word(conn, question, k)`: the same for the passages that hold any of its words: the query `plainto_tsquery('english', question)` gives, with each `&` made `|`.

Send `question` and `k` to Postgres as the query's parameters.

```
index(conn)
every_word(conn, question, k=5) -> list of ids
any_word(conn, question, k=5) -> list of ids
```
