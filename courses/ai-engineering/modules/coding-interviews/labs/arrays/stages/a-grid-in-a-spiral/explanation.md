```python
def spiral(grid):
    if not grid:
        return []
    order = []
    top, bottom, left, right = 0, len(grid) - 1, 0, len(grid[0]) - 1
    while top <= bottom and left <= right:
        order.extend(grid[top][left : right + 1])
        order.extend(grid[row][right] for row in range(top + 1, bottom + 1))
        if top < bottom:
            order.extend(
                grid[bottom][column] for column in range(right - 1, left - 1, -1)
            )
        if left < right:
            order.extend(grid[row][left] for row in range(bottom - 1, top, -1))
        top, bottom, left, right = top + 1, bottom - 1, left + 1, right - 1
    return order
```

The four bounds mark the ring being read. Each ring reads its top row, its right column below that, its bottom row back from the corner and its left column up, and then every bound moves in by one. The two checks keep a ring of one row from reading that row again as its bottom row, and a ring of one column from reading it again as its left column. Every value is read once, so the time grows with the number of values.

The work is in the edges, so try a grid of one row, one of one column, one of one value, and grids wider than they are tall and taller than they are wide.
