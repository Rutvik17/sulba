Count first, then rank: a query in a `WITH` clause can count each zone's trips with `GROUP BY`, and a query after it ranks the counts. `pickup_at >= %(start)s AND pickup_at < %(end)s`, with `end` the day after `day`, takes a day's trips.

---

`rank() OVER (PARTITION BY borough ORDER BY trips DESC)` ranks each borough's zones apart from the others'. Postgres doesn't allow a window function in `WHERE`, so rank in one query and keep the ranks up to `n` in the one after it.

---

`percentile_cont(0.5) WITHIN GROUP (ORDER BY fare)` is the median, and `sum(trips) OVER (PARTITION BY borough)` each borough's trips beside each of its zones. Make one side of the share a `float8`, or Postgres divides whole numbers.
