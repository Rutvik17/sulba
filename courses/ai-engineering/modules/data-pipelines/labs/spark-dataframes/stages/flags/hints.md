Build each flag as a column: `F.col("distance") <= 0`, `F.col("dropoff_at") < F.col("pickup_at")`. A dict of each flag's name and its column, in the order of `FLAGS`, keeps them in one place. `F.expr("INTERVAL 24 HOURS")` added to a time is the time a day later.

---

A comparison with a missing value is missing, not false. `F.coalesce(flag, F.lit(False))` makes it false, and `select("*", *flags)` adds the flags after the trips' columns.

---

`clean` is true when no flag is: `~F.greatest(*flags)` once each flag is true or false. For the counts, one `agg` with `F.count_if(F.col(name))` for each column counts them all in one query.
