`ConnectionPool(url, min_size=1, max_size=..., kwargs={"autocommit": True}, open=False)` makes a pool, `pool.open(wait=True, timeout=10)` opens it and waits for its first connection, and `pool.close()` closes it.

---

`percentile_cont(0.9) WITHIN GROUP (ORDER BY seconds)` is the 90th percentile of a group's seconds, and `count(*) FILTER (WHERE outcome = 'done')` counts the turns that were done.

---

`(started_at AT TIME ZONE 'UTC')::date` is the day a turn started on, in UTC. A condition on `started_at` itself can use the index on it, and one on a value worked out from it can't.
