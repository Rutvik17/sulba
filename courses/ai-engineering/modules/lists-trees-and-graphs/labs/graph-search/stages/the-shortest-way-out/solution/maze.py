from collections import deque


def shortest_way(rows):
    """The fewest steps from the maze's start, `S`, to its exit, `E`, or -1 if there's no way
    there."""
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
