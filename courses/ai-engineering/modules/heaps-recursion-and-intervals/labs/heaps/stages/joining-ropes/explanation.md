```python
import heapq


def join_cost(lengths):
    ropes = list(lengths)
    heapq.heapify(ropes)
    cost = 0
    while len(ropes) > 1:
        joined = heapq.heappop(ropes) + heapq.heappop(ropes)
        cost += joined
        heapq.heappush(ropes, joined)
    return cost
```

Each rope's length is paid once for every join it's part of, so the longest ropes should go through the fewest joins: joining the two shortest each time gives the least cost, and the tests check it against trying every order of joins on small lists. A heap gives the two shortest in time in proportion to the logarithm of the ropes, and takes the joined rope back the same way, so the {% $fig.joins %} joins of the longest test take time in proportion to n log n.

Finding the two shortest by looking through every rope left, for each join, is the slow way: {% $fig.looks %} looks for the longest test.
