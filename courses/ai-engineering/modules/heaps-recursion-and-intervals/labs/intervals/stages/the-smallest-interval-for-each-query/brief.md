`intervals` is a list of intervals `(left, right)`, each holding every whole number from `left` to `right`, both included, so its size is `right - left + 1`. Write `smallest_containing`:

```
smallest_containing(intervals, queries) -> for each query, in order, the size of the smallest
    interval that holds it, or -1 when none does
```

`smallest_containing([(1, 4), (2, 4), (3, 6), (4, 4)], [2, 3, 4, 5])` returns `[3, 3, 1, 4]`. The tests' longest lists have {% $fig.intervals %} intervals and {% $fig.queries %} queries.
