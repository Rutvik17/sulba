```python
import heapq


def medians(numbers):
    low, high = [], []
    found = []
    for number in numbers:
        if low and number > low[0]:
            heapq.heappush(high, number)
        else:
            heapq.heappush_max(low, number)
        if len(low) > len(high) + 1:
            heapq.heappush(high, heapq.heappop_max(low))
        elif len(high) > len(low):
            heapq.heappush_max(low, heapq.heappop(high))
        if len(low) > len(high):
            found.append(float(low[0]))
        else:
            found.append((low[0] + high[0]) / 2)
    return found
```

Every number of the smaller half is at most every number of the larger, and the smaller half has as many as the larger or one more. So the median is the smaller half's largest, or the mean of the two halves' tops, and each heap keeps its top at index 0. A new number goes into the half it belongs to, and at most one number moves across to keep the sizes in step, each step taking time in proportion to the logarithm of the numbers so far.

`heappush_max` and `heappop_max` are new in Python 3.14. Before them, the usual way to keep a max-heap was to push negated numbers onto a min-heap.

Sorting the numbers so far after each new one is the slow way: for the longest test, {% $fig.sorted %} numbers sorted in all.
