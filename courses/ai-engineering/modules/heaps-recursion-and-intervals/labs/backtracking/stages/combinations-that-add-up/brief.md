`numbers` is a list of positive whole numbers, some of them equal, and `target` is a positive whole number. Write `totals`:

```
totals(numbers, target) -> every combination of the numbers that adds up to target
```

Each place in `numbers` can be used once, and combinations of the same numbers count once. Each combination is a tuple of its numbers from smallest to largest, and the list goes from smallest to largest too. `totals([10, 1, 2, 7, 6, 1, 5], 8)` returns `[(1, 1, 6), (1, 2, 5), (1, 7), (2, 6)]`. The tests' longest list has {% $fig.numbers %} numbers.
