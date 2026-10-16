def spiral(grid):
    """Every value, clockwise from the top left corner, ring by ring inwards."""
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
