Write `merge_sorted`:

```
merge_sorted(lists) -> every number in lists, each sorted from smallest to largest, in one
    sorted list
```

`merge_sorted([[1, 4, 9], [2, 3, 10], [5]])` returns `[1, 2, 3, 4, 5, 9, 10]`. Some lists can be empty, and the lists are sorted already, so don't sort the numbers again: merge them.

The tests' longest case has {% $fig.lists %} lists of {% $fig.length %} numbers.
