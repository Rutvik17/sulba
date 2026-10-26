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
