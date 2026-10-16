Write `shortest_reach`, for a list of positive numbers and a positive target:

```
shortest_reach(numbers, target) -> the length of the shortest run of adjacent numbers whose sum
    is at least target, or 0 if no run reaches it
```

`shortest_reach([2, 1, 5, 2, 3, 2], 7)` returns `2`, for `[5, 2]`, and `shortest_reach([1, 1, 1], 5)` returns `0`.

The tests' longest list has {% $fig.numbers %} numbers.
