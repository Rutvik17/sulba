Write `most_frequent`:

```
most_frequent(items, k) -> the k items that appear most often, the most frequent first, and items
    that appear equally often in the order they first appear
```

`most_frequent(["b", "a", "c", "a", "b", "a", "d"], 2)` returns `["a", "b"]`, and with `k` of `3` it returns `["a", "b", "c"]`: `c` and `d` appear once each, and `c` comes first. Each test has `1 <= k` and no more than the number of different items.

The tests' longest list has {% $fig.items %} items, of {% $fig.kinds %} different ones.
