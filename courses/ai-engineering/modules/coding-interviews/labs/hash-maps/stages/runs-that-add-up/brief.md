Write `count_runs`:

```
count_runs(numbers, target) -> how many runs of one or more adjacent numbers add up to target
```

`count_runs([2, -1, 3, -1, 2], 3)` returns `3`: the runs `[2, -1, 3, -1]`, `[-1, 3, -1, 2]` and `[3]`. Numbers can be negative, so a run's sum can go down as it grows.

The tests' longest list has {% $fig.numbers %} numbers.
