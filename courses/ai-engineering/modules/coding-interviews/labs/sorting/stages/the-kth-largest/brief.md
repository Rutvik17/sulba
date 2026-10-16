Write `kth_largest`:

```
kth_largest(numbers, k) -> the kth largest of numbers, counting repeats
```

With `k` of `1` it's the largest. `kth_largest([3, 9, 2, 9, 5], 2)` returns `9`, since the two `9`s count as two, and `kth_largest([3, 9, 2, 9, 5], 3)` returns `5`. Each test has `1 <= k <= len(numbers)`.

The tests' longest list has {% $fig.numbers %} numbers, with `k` of {% $fig.k %}.
