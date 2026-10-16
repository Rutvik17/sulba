Write `pair_sum`, which finds two numbers in a list that add up to a target:

```
pair_sum(numbers, target) -> the positions (i, j), with i < j, of two numbers that add up to
    target, or None if no two do
```

A number can't pair with itself, though two equal numbers can pair. When several pairs add up to the target, return the one that ends first, and of those, the one that starts first. `pair_sum([5, 2, 9, 6, 3], 8)` returns `(1, 3)`, since `2 + 6` ends before `5 + 3`.

The tests' longest list has {% $fig.numbers %} numbers.
