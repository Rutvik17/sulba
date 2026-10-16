```python
def rooms_needed(meetings):
    starts = sorted(start for start, _ in meetings)
    ends = sorted(end for _, end in meetings)
    rooms = most = ended = 0
    for start in starts:
        while ends[ended] <= start:
            ended += 1
            rooms -= 1
        rooms += 1
        most = max(most, rooms)
    return most
```

The rooms in use go up only when a meeting starts, so the most in use at once is found at a start: there, every meeting that ended at or before it has freed its room, and every one that started before it and hasn't ended holds one. Which meeting holds which room doesn't matter, only how many are busy, so the starts and the ends can be sorted apart. A meeting ends after it starts, so every end the loop passes belongs to a meeting already counted. Sorting takes time in proportion to `$n \log n$`, and the pass `n`.

A min-heap of the end times of the meetings in progress gives the same answer, also in time in proportion to `$n \log n$`. Counting the meetings going on at each start, by checking every meeting, makes {% $fig.checks %} checks for the longest test's {% $fig.meetings %} meetings, far past the time limit.
