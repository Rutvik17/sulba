```python
import heapq


def smallest_containing(intervals, queries):
    intervals = sorted(intervals)
    found = {}
    reach = []
    place = 0
    for query in sorted(set(queries)):
        while place < len(intervals) and intervals[place][0] <= query:
            left, right = intervals[place]
            heapq.heappush(reach, (right - left + 1, right))
            place += 1
        while reach and reach[0][1] < query:
            heapq.heappop(reach)
        found[query] = reach[0][0] if reach else -1
    return [found[query] for query in queries]
```

Taken in sorted order, each query can use every interval that starts at or before it, so the intervals join the heap once each, by their left ends. An interval whose right end is before the query can't hold it or any later query, so it can leave whenever it reaches the top. The heap is ordered by size, so once its top holds the query, that's the smallest interval that does: the ones still below it that have ended don't matter, since they're larger. Each interval joins and leaves the heap at most once, so with the sorts the work takes time in proportion to n log n, and the answers go back in the queries' own order through a dict.

Checking every interval for every query is the slow way: {% $fig.pairs %} checks for the longest test.
