The help desk's search page shows, beside its answer, the nearest passages from each service, under the service's name, so that someone can see what each one says. `WHERE domain = %s` keeps one service's passages, but through the index, Postgres keeps those of the candidates the index finds: in a service other than the one a question is about, few are left, and often none.

In `service.py`, write:

- `search_in(conn, vector, domain, k, ef_search)`: the ids of the `k` passages of the service `domain` nearest to `vector`, nearest first, through the index. Turn on pgvector's iterative index scans for this search alone, in relaxed order, so that the scan goes on until it has `k`. Find the rows in a materialized CTE, and sort them by distance in the query around it.
- `by_service(conn, vector, k)`: each service's `k` nearest passages, from `search_in`, in a dict under the service's name, for every service in the table.

```
search_in(conn, vector, domain, k=10, ef_search=40) -> list of ids
by_service(conn, vector, k=5) -> dict of service: list of ids
```
