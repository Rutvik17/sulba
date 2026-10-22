`generate_series(start, end - interval '1 hour', interval '1 hour')` gives the day's 24 hours as timestamps. Count the zone's trips by `date_trunc('hour', pickup_at)` in a query of its own, then `LEFT JOIN` the counts onto the hours, so that every hour keeps its row, and `coalesce(trips, 0)` gives 0 where no count matched.

---

A window function over `ORDER BY hour` takes, by default, every row from the first to the current one: right for the running total, not for the mean of three hours. `ROWS BETWEEN 2 PRECEDING AND CURRENT ROW` takes the current row and the two before it. `lag(trips) OVER (ORDER BY hour)` gives the hour before's.

---

Postgres's `sum` and `avg` of whole numbers give `numeric`, which psycopg returns as Python's `Decimal`. Cast them in the query: `::bigint` for the running total, `::float8` for the mean.
