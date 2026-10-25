`spark.range(31)` gives an `id` from 0 to 30, and `F.date_add(F.lit("2025-08-01").cast("date"), F.col("id").cast("int"))` turns each into a day. For the boroughs, `F.when(~F.col("Borough").isin(MISSING), F.col("Borough"))` keeps every borough but those.

---

`august(spark).crossJoin(names)`, where `names` holds each borough once, gives every borough on every day. Join the clean trips to the zones on `pickup_zone`, then count them by `F.to_date("pickup_at")` and borough.

---

Join the counts and the weather to that grid with `"left"`, so a row with no match stays, and use `F.coalesce("trips", F.lit(0))` for its trips. `F.date_format("day", "EEEE")` gives the weekday's name.
