```python
import heapq


def merge_sorted(lists):
    heap = [(numbers[0], which, 0) for which, numbers in enumerate(lists) if numbers]
    heapq.heapify(heap)
    merged = []
    while heap:
        number, which, at = heapq.heappop(heap)
        merged.append(number)
        if at + 1 < len(lists[which]):
            heapq.heappush(heap, (lists[which][at + 1], which, at + 1))
    return merged
```

The heap holds the next number of every list with numbers left, so its smallest is the next number of the merged list. Popping it and pushing the number after it from the same list keeps that true. Each entry carries its list and position, which also settles ties between equal numbers without comparing the lists themselves. With `N` numbers in `k` lists, each pop and push takes time in proportion to `$\log k$`: `$N \log k$` in all, with `k` entries of space besides the answer. `heapq.merge` does the same.

Finding the smallest next number by looking at every list, for each number, makes {% $fig.looks %} looks for the longest case, far past the time limit.
