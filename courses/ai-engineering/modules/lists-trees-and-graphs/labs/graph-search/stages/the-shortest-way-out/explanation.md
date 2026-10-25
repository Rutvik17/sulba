```python
from collections import deque


def shortest_way(rows):
    start = next(
        (y, x)
        for y, row in enumerate(rows)
        for x, square in enumerate(row)
        if square == "S"
    )
    steps = {start: 0}
    waiting = deque([start])
    while waiting:
        y, x = waiting.popleft()
        if rows[y][x] == "E":
            return steps[y, x]
        for near in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)):
            ny, nx = near
            open_ = (
                0 <= ny < len(rows) and 0 <= nx < len(rows[ny]) and rows[ny][nx] != "#"
            )
            if open_ and near not in steps:
                steps[near] = steps[y, x] + 1
                waiting.append(near)
    return -1
```

A breadth-first search takes squares in the order they were reached, so it finishes every square 1 step away before any 2 steps away, and so on: the first time it reaches a square is by a shortest way, and the exit's steps when it's taken are the answer. Each square goes into the queue once, so the time and space are in proportion to the squares.

A depth-first search finds a way out, but not the shortest one. Trying every way and keeping the shortest is the slow way: through a fully open 5 by 5 square there are already {% $fig.paths %} ways from one corner to the opposite one that never revisit a square, and each row and column added multiplies them. The queue is a `deque` because, as Python's tutorial puts it, a list is slow at the front: "doing inserts or pops from the beginning of a list is slow (because all of the other elements have to be shifted by one)".
