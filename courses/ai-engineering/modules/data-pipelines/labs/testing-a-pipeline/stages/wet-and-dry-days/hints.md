Group by borough. `F.count_if(F.col("wet"))` counts the wet days, and `F.avg(F.when(F.col("wet"), F.col("trips")))` averages their trips, since `when` without `otherwise` leaves every other day missing and `avg` passes over missing values.

---

For the comparison, a window over `Window.partitionBy("borough", "weekday")` with no ordering covers every day of the borough's weekday. `F.avg(F.when(~F.col("wet"), F.col("trips"))).over(window)` gives each row the mean of that weekday's dry days.

---

Work out `dry_days` and `dry_trips` on every row first, then keep the wet ones with `.where("wet")`: filtering first would leave the window no dry days to see.
