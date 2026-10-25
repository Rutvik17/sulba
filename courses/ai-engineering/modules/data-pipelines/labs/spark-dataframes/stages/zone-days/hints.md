`spark.read.option("header", True).csv(path)` reads every column as a string, so cast the zone's number to an int. `F.when(~F.col(name).isin(MISSING), F.col(name))` keeps each value but those, which it leaves missing.

---

Group the clean trips by zone and `F.to_date("pickup_at")` and count them. A window `Window.partitionBy("zone").orderBy(days).rangeBetween(-6, 0)` covers the seven days ending each day when `days` is a number of days, such as `F.datediff("day", F.lit("2025-08-01").cast("date"))`.

---

Sum the trips over that window and divide by 7, so a day missing from the rows counts as 0, and give the first six days no `week` with `F.when`. For the places, `F.rank().over(Window.partitionBy("borough", "day").orderBy(F.desc("trips")))`, then keep the rows placed `n` or better. `F.broadcast(zones)` in the join marks the zones as small.
