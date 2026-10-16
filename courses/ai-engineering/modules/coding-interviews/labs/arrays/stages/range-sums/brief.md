Write `range_sums`, which sums many ranges of one list of numbers:

```
range_sums(numbers, ranges) -> the sum of numbers[start:stop] for each (start, stop) in ranges
```

Each range has `0 <= start <= stop <= len(numbers)`, and a range with `start == stop` holds no numbers. `range_sums([3, -1, 4, 1, 5], [(0, 2), (1, 4), (2, 2)])` returns `[2, 4, 0]`.

The tests' longest list has {% $fig.numbers %} numbers, with {% $fig.ranges %} ranges.
