```python
def most_frequent(items, k):
    counts = {}
    for item in items:
        counts[item] = counts.get(item, 0) + 1
    return sorted(counts, key=lambda item: -counts[item])[:k]
```

The dict counts each item in one pass and keeps the items in the order they first appear. Sorting by count, largest first, keeps that order among items that tie, since Python's sort is stable, so the first `k` are the answer. Counting takes time in proportion to the `n` items, and sorting the `d` different ones `$d \log d$`. `collections.Counter(items).most_common(k)` gives the same order.

Counting each different item with `items.count(item)` reads the whole list once for each of them: for the longest test, {% $fig.reads %} reads, far past the time limit.
