```python
def fewest_removed(meetings):
    kept, last_end = 0, None
    for start, end in sorted(meetings, key=lambda meeting: meeting[1]):
        if last_end is None or start >= last_end:
            kept += 1
            last_end = end
    return len(meetings) - kept
```

Keeping the most meetings is the same as removing the fewest. The meeting that ends first is safe to keep: any set of meetings that don't overlap can swap its first meeting for this one and still not overlap, since this one ends no later. After it, the same holds for the meetings that start once it's over, so taking meetings by end, each that starts no earlier than the last one kept ends, keeps the most. The sort takes time in proportion to n log n, and the pass after it n.

Trying every set of meetings to keep is the slow way: n meetings have $2^n$ sets, {% $fig.subsets %} for just {% $fig.few %} meetings.
