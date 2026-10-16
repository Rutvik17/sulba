Write `longest_streak`:

```
longest_streak(numbers) -> the length of the longest streak of consecutive integers among
    numbers, which come in any order
```

`longest_streak([10, 5, 12, 3, 11, 4, 13, 20])` returns `4`, for `10, 11, 12, 13`. A number repeated counts once, and an empty list has no streak, so it gives `0`.

The tests' longest list has {% $fig.numbers %} numbers. Sorting them first takes time in proportion to `$n \log n$`: find a way in proportion to `n`.
