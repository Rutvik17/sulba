Write `largest_run`, which finds the largest sum of adjacent numbers in a list:

```
largest_run(numbers) -> the largest sum of a run of one or more adjacent numbers
```

A run holds at least one number, so when every number is negative, so is the answer. `largest_run([2, -5, 4, -1, 3, -6, 2])` returns `6`, the sum of `[4, -1, 3]`.

Each list in the tests holds at least one number, and the longest holds {% $fig.numbers %}.
