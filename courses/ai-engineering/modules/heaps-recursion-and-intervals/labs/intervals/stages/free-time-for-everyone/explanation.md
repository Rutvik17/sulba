```python
import heapq


def free_time(schedules):
    busy = heapq.merge(*schedules)
    found = []
    first = next(busy, None)
    if first is None:
        return found
    end = first[1]
    for start, finish in busy:
        if start > end:
            found.append((end, start))
        end = max(end, finish)
    return found
```

Every schedule is sorted already, so `heapq.merge` gives all the busy times in order of start without sorting them again, holding one busy time from each person at a time. The latest end so far is when everyone busy until then is free, so a busy time that starts after it leaves a gap from that end to its start, and one that starts no later only pushes the end on. Each busy time takes time in proportion to the logarithm of the people.

Marking every moment from the earliest start to the latest end is the slow way: up to {% $fig.span %} of them for the longest test.
