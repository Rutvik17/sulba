```python
from collections import Counter


def longest_with_kinds(items, k):
    counts = Counter()
    start = best = 0
    for end, item in enumerate(items):
        counts[item] += 1
        while len(counts) > k:
            counts[items[start]] -= 1
            if counts[items[start]] == 0:
                del counts[items[start]]
            start += 1
        best = max(best, end - start + 1)
    return best
```

`counts` holds how many of each value the window has, and a value leaves it when its count reaches zero, so `len(counts)` is the number of different values in the window. When a new item makes too many, the window drops items from its start until it has `k` again. Each item joins the window once and leaves it at most once: time in proportion to the list, and space in proportion to `k`.

Growing a run from every start until it holds too many values reads {% $fig.reads %} items for the longest test, far past the time limit.
