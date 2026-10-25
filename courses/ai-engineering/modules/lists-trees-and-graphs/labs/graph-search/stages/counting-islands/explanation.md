```python
def islands(rows):
    seen, count = set(), 0
    for top, row in enumerate(rows):
        for left, square in enumerate(row):
            if square != "#" or (top, left) in seen:
                continue
            count += 1
            seen.add((top, left))
            waiting = [(top, left)]
            while waiting:
                y, x = waiting.pop()
                for near in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)):
                    ny, nx = near
                    land = (
                        0 <= ny < len(rows)
                        and 0 <= nx < len(row)
                        and rows[ny][nx] == "#"
                    )
                    if land and near not in seen:
                        seen.add(near)
                        waiting.append(near)
    return count
```

Each square of land that no counted island holds starts an island, and a flood from it marks every square joined to it, so the island is counted once. Taking squares from the end of the list makes the flood a depth-first search, and from the front, with a `deque`, a breadth-first one: either reaches every square of the island. Every square is looked at once and every square of land is added once, so the time is in proportion to the squares, and the space to the land.

The same flood written as a function that calls itself on each neighbour goes one call deeper for each square along its way. On the largest test's island that's up to {% $fig.cells %} calls deep, past the recursion limit Python starts with, which, in `sys.setrecursionlimit`'s documentation, "prevents infinite recursion from causing an overflow of the C stack and crashing Python". A list of squares to visit keeps the depth in data, where it can grow as far as memory allows.
