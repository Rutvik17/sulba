`first` and `second` are lists of numbers in order. Write `smallest_pairs`:

```
smallest_pairs(first, second, k) -> the k pairs (a, b), a from first and b from second, with
    the smallest sums, smallest first
```

Pairs whose sums are equal come in the order of `a`'s place in `first`, then `b`'s in `second`. `smallest_pairs([1, 7, 11], [2, 4, 6], 3)` returns `[(1, 2), (1, 4), (1, 6)]`. With fewer than k pairs, it gives them all. The tests' longest lists have {% $fig.size %} numbers each, with k at {% $fig.k %}.
