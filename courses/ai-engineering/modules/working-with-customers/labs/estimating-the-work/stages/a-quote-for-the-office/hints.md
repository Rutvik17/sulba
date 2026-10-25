Your `promised(finishes, 0.8)` gives the 80th percentile. `math.ceil` takes it up to whole days.

---

Step a day at a time from the start, counting the days whose `weekday()` is below 5 and that aren't in `days_off`, until the count reaches the quote's days.

---

For each milestone, `price * share // total` is its payment rounded down, and `price * share % total` says how much it lost: the larger, the sooner it gets a cent back.
