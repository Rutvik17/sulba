```python
def merge_intervals(intervals):
    merged = []
    for start, end in sorted(intervals):
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))
    return merged
```

Sorted by start, the intervals that merge together come one after another, so each interval only has to be compared with the last merged one: it joins it when it starts at or before its end, and the merged end is the larger of the two, since an interval can lie inside another. Sorting takes time in proportion to `$n \log n$`, the pass `n`, and the merged list as much space.

Comparing every pair of intervals, and merging any two that overlap until none do, makes {% $fig.pairs %} comparisons in a single pass for the longest test's {% $fig.intervals %} intervals, far past the time limit.
