```python
import heapq


def furthest(heights, bricks, ladders):
    """The furthest building reached from the first, climbing each step up with a ladder or with
    as many bricks as the step is high."""
    laddered = []
    for place in range(len(heights) - 1):
        step = heights[place + 1] - heights[place]
        if step <= 0:
            continue
        heapq.heappush(laddered, step)
        if len(laddered) > ladders:
            bricks -= heapq.heappop(laddered)
            if bricks < 0:
                return place
    return len(heights) - 1
```

Of the steps up to any building, the ladders should take the highest and the bricks the rest, so a building can be reached when the steps outside the ladders' share add up to no more than the bricks. Walking the row, a min-heap holds the steps the ladders take. Each step up joins it, and once it holds one more than the ladders, its smallest step leaves for the bricks. The first time the bricks run out, the building before that step is the furthest. Each step goes in and out of a heap no larger than the ladders plus one, so the walk takes time in proportion to `$n \log L$` for `$n$` buildings and `$L$` ladders.

Spending bricks on each step until they run out, then the ladders, is wrong when a high step comes first: on `[0, 10, 11, 12]` with 10 bricks and one ladder, it spends the bricks on the step of 10 and stops at building 2, where the ladder on that step and the bricks on the two after reach building 3. Checking each building in turn by sorting the steps up to it is right but slow: for the tests' longest row, {% $fig.sorted %} steps sorted.
