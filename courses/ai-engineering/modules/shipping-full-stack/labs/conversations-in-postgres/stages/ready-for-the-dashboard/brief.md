In `app.py`, put the desk together on Postgres, as The desk's API put it together in memory, so that `uv run uvicorn app:create_app --factory` serves it:

- `settings_from(environ)` gives the settings, now with `DESK_DATABASE_URL`, the database's address, which has no default.
- As the app starts, `create_app` opens a `ConnectionPool` to the database, with autocommit connections, enough for every running reply and a few more requests. It waits for the first connection and applies the migrations. It keeps the pool in `app.state.pool`, and a `Store` on it in `app.state.conversations`, beside the client, desk, gate and agents as before. As the app stops, it closes the pool.
- `GET /usage?days=7` gives each day's usage, as a `Day`, for each of the last `days` days that has turns, today's included. A day's usage is its number of turns, how many of them were done, their tokens of prompt and of reply, and the median and 90th percentile of their seconds. `days` is from 1 to 90.

What the app must do:

- refuse settings without a database, or with one that isn't Postgres, naming the variable;
- keep its conversations from one run to the next, and close its connections as it stops;
- count each day's turns in UTC, whatever the database's time zone;
- find a week's turns through the index on `started_at`, rather than by reading every turn.

How it does so is yours to choose.

```
settings_from(environ) -> Settings
create_app(settings=None, data=Path("data"), client=None) -> FastAPI
GET /usage?days=7
```

Three tests run on every attempt. Then four checks run before the code ships.

With `DESK_DATABASE_URL` set to the address `uv run sulba.py db` prints, and the models running, the app serves the desk on the lab's database.
