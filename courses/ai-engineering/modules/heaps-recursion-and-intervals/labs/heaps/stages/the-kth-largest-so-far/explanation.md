```python
import heapq


class KthLargest:
    def __init__(self, k, numbers):
        self.k = k
        self.largest = heapq.nlargest(k, numbers)
        heapq.heapify(self.largest)

    def add(self, number):
        if len(self.largest) < self.k:
            heapq.heappush(self.largest, number)
        elif number > self.largest[0]:
            heapq.heapreplace(self.largest, number)
        return self.largest[0]
```

A number smaller than the k largest so far can never be the kth largest again, since numbers are only added. So the stream keeps just the k largest, in a min-heap whose top is the kth largest: a new number replaces the top if it's larger, and is dropped otherwise. Each add takes time in proportion to the logarithm of k, and the stream holds k numbers, however many it's given.

Sorting every number so far for each one added is the slow way: {% $fig.sorted %} numbers sorted in all for the longest test.
