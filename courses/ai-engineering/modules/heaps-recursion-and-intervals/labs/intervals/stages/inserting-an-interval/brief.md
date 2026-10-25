`intervals` is a list of intervals `(start, end)`, sorted by start, none of them overlapping, and `new` is one more. Each holds every number from its start to its end, both included, so two intervals that share a number overlap. Write `inserted`:

```
inserted(intervals, new) -> the intervals with new among them, overlapping ones merged
```

`inserted([(1, 3), (6, 9)], (2, 5))` returns `[(1, 5), (6, 9)]`, and `inserted([(1, 2), (3, 5), (6, 7), (8, 10), (12, 16)], (4, 8))` returns `[(1, 2), (3, 10), (12, 16)]`. The tests' longest list has {% $fig.intervals %} intervals.
