`first` and `second` are lists of intervals `(start, end)`, each list sorted and none of its intervals overlapping. Each interval holds every number from its start to its end, both included. Write `common`:

```
common(first, second) -> the intervals both lists cover, sorted
```

`common([(0, 2), (5, 10), (13, 23), (24, 25)], [(1, 5), (8, 12), (15, 24), (25, 26)])` returns `[(1, 2), (5, 5), (8, 10), (15, 23), (24, 24), (25, 25)]`. The tests' longest lists have {% $fig.intervals %} intervals each.
