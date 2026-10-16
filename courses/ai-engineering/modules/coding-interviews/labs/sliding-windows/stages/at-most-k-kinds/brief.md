Write `longest_with_kinds`:

```
longest_with_kinds(items, k) -> the length of the longest run of adjacent items holding at most k
    different values
```

`longest_with_kinds(["a", "b", "a", "c", "c", "a", "b"], 2)` returns `4`, for `["a", "c", "c", "a"]`. With `k` of `0`, no item fits in a run, so the answer is `0`.

The tests' longest list has {% $fig.items %} items.
