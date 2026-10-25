```python
import heapq


def smallest_pairs(first, second, k):
    if not first or not second:
        return []
    frontier = [(first[i] + second[0], i, 0) for i in range(min(k, len(first)))]
    heapq.heapify(frontier)
    pairs = []
    while frontier and len(pairs) < k:
        _, i, j = heapq.heappop(frontier)
        pairs.append((first[i], second[j]))
        if j + 1 < len(second):
            heapq.heappush(frontier, (first[i] + second[j + 1], i, j + 1))
    return pairs
```

Picture the pairs as a grid, row `i` for `first[i]` and column `j` for `second[j]`: along a row the sums only grow. So the next smallest pair is always the next untaken pair of some row, and the heap holds one candidate per row, its sum and places deciding the order the brief asks for. Only the first k rows can hold any of the k smallest, since each of those rows' first pair is no larger than any pair of a later row. Each pair taken costs time in proportion to the logarithm of k.

Working out every pair's sum and sorting them is the slow way: {% $fig.pairs %} pairs for the longest test.
