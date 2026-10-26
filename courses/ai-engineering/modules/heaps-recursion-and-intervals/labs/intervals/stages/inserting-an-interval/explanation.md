```python
def inserted(intervals, new):
    start, end = new
    found = []
    place = 0
    while place < len(intervals) and intervals[place][1] < start:
        found.append(intervals[place])
        place += 1
    while place < len(intervals) and intervals[place][0] <= end:
        start = min(start, intervals[place][0])
        end = max(end, intervals[place][1])
        place += 1
    found.append((start, end))
    found.extend(intervals[place:])
    return found
```

The list is in order and its intervals don't overlap, so it falls into three runs: those that end before the new interval starts, those that overlap it, and those that start after it ends. The first run is copied as it is, the second is merged into the new interval, each one widening its ends, and the third follows the merged interval. Each interval is looked at once, so an insert takes time in proportion to the list's length, with no sort.
