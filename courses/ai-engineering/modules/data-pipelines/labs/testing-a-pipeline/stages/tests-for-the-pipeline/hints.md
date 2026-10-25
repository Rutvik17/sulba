Take one requirement of each function at a time, and give it the smallest input that shows it: one day of weather, two trips, three daily rows.

---

A line of the weather file in the service's layout, for a day with 18.0 mm of rain and a failed high:

```
"USW00094728","2025-08-13","   20",",,W","  180",",,W,2400","    0",",,W,2400","  999",",X,W","  200",",,W",,,,,,
```

The header is the first line of `data/central-park-2025-08.csv`.

---

Test the edges the brief draws: a day with exactly 1.0 mm, a borough with no trips on a day, a wet day whose weekday has other dry days than the rest of the week.
