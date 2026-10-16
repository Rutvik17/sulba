An interval is a pair `(start, end)` with `start <= end`. Two intervals overlap when they share any point, so `(1, 3)` and `(3, 5)` overlap too. Write `merge_intervals`:

```
merge_intervals(intervals) -> the intervals, with every two that overlap merged into one, sorted
    by start
```

`merge_intervals([(4, 7), (1, 3), (9, 12), (2, 5), (12, 14)])` returns `[(1, 7), (9, 14)]`.

The tests' longest list has {% $fig.intervals %} intervals.
