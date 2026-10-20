The help desk keeps its pages in Postgres, and pgvector, an extension of Postgres, can keep each passage's vector in a column beside its text and search the vectors in SQL. This lab moves the help desk's search there, with the vectors nomic-embed-text-v1.5 gave its {% $fig.passages %} passages and its questions. `uv run sulba.py db` starts the lab's database on your machine, with pgvector installed, and each test gets a new, empty one.

In `store.py`, write:

- `connect(url)`: a connection to the database at `url`, through psycopg, in autocommit mode, so that each statement takes effect as it runs. Call `register_vector(conn)` from the `pgvector` package on it: NumPy arrays then go to Postgres as vectors, and vectors come back as pgvector's `Vector`.
- `create(conn)`: the table `passages`, with each passage's `id`, its service in `domain`, its `page`, its text in `body`, all `text`, and its vector in `embedding`, a `vector(768)` kept in its row with `STORAGE PLAIN`. The id is the table's primary key, and no column can be null.
- `load(conn, rows)`: the rows, each a passage's id, domain, page, body and vector as a float32 NumPy array, into the table with one `COPY` in its binary format, then `ANALYZE` on the table.
- `nearest(conn, vector, k)`: the ids of the `k` passages nearest to `vector` by cosine distance, pgvector's `<=>`, nearest first.

Send `vector` and `k` to Postgres as the query's parameters, never inside its text.

```
connect(url) -> psycopg.Connection
create(conn)
load(conn, rows)
nearest(conn, vector, k=10) -> list of ids
```
