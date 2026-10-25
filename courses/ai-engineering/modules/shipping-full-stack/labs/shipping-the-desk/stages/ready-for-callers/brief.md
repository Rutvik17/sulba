The desk's `/health` says the process is up, and asks nothing else. A host also needs to know when the desk can serve callers: once its database answers and its model has loaded, which can take a while after the desk starts.

In `health.py`, write the checks, each an async function that returns once what it checks answers and raises otherwise:

- `database_check(pool)`, a check that the database answers `SELECT 1`, on a connection from the pool, waiting at most `CHECK_SECONDS` for one.
- `model_check(client)`, a check that the model's server has loaded the model: its `/health` answers 200, and 503 while the model loads, which fails the check with `The model is still loading.`. Any other error status fails it too.
- `readiness(checks, seconds)`, the state of each check by its name: `ok`, or what went wrong, the error's message or, when it has none, its type's name. The checks run at once, and each has `seconds`, after which its state is `No answer in 2 seconds.`, with its own seconds.
- `GET /ready` on `router`, which runs the desk's checks, `database` on `app.state.pool` and `model` on `app.state.client`, and answers 200 with `{"checks": {...}}` when every one is `ok`. Otherwise it answers 503 with problem details, as `application/problem+json`: `type`, `title`, `status`, a `detail` that names each check that isn't ok, such as `Not ready: model.`, and the `checks`.

```python
database_check(pool: ConnectionPool) -> Check
model_check(client: httpx.AsyncClient) -> Check
readiness(checks: Mapping[str, Check], seconds: float = CHECK_SECONDS) -> dict[str, str]
```

The tests give the database check a database of the runner's, and stand in for the model's server.
