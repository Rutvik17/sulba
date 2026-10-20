pgvector's documentation gives a vector's storage as `4 * dimensions + 8` bytes, each number a float32, so each of the help desk's vectors, of {% $fig.dimensions %} numbers, takes {% $fig.bytes %} bytes. Binary `COPY` sends them in those bytes, every row in one statement, where the text format would write each number in decimal and Postgres would read it back; pgvector's documentation recommends `COPY` for bulk loading.

Postgres moves values out of a row wider than {% $fig.toast %} into a table beside it, which its documentation calls TOAST, and pgvector lets it move vectors there. Its planner, which chooses how to run each query from what each way would cost, leaves that table out of what reading every row costs, as pgvector's documentation notes. With the vectors moved out, it reads every passage even once the next stage's index is built, though the index finds them faster. `STORAGE PLAIN` keeps each vector in its row, as pgvector's documentation suggests, where the planner counts it.

The planner's choices rest on statistics about each table, such as how many rows it has and how often each value comes, which `ANALYZE` gathers. Postgres's documentation recommends running it after loading many rows: with no statistics, the planner can choose badly.

`<=>` is cosine distance: 1 less the cosine of the angle between two vectors, so the nearest passage has the smallest. With no index, Postgres works out the distance to every row and keeps the `k` smallest, which pgvector's documentation calls exact nearest neighbor search, with "perfect recall". The next stage gives some of that up for speed.

A parameter goes to Postgres apart from the query's text, so nothing in it can change the query. psycopg sends `%s` placeholders' values that way, and `register_vector` gives it pgvector's types to send NumPy arrays as. In autocommit mode, each statement is its own transaction; a block that needs several in one, as the next stages do, opens it with `conn.transaction()`.

With the lab's database running, from `uv run sulba.py db` in another terminal, your code can use it with the address it prints:

```python
from store import connect, create

with connect("postgresql://postgres:...@127.0.0.1:5432/postgres") as conn:
    create(conn)
    print(conn.execute("SELECT count(*) FROM passages").fetchone())
```
