```python
def captured(board):
    rows, columns = len(board), len(board[0]) if board else 0
    safe = set()
    stack = [
        (r, c)
        for r in range(rows)
        for c in range(columns)
        if board[r][c] == "O" and (r in (0, rows - 1) or c in (0, columns - 1))
    ]
    while stack:
        r, c = stack.pop()
        if (r, c) in safe:
            continue
        safe.add((r, c))
        for nr, nc in ((r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)):
            if (
                0 <= nr < rows
                and 0 <= nc < columns
                and board[nr][nc] == "O"
                and (nr, nc) not in safe
            ):
                stack.append((nr, nc))
    return [
        "".join("O" if (r, c) in safe else "X" for c in range(columns))
        for r in range(rows)
    ]
```

A region is safe exactly when it touches the edge, so a search from every `O` on the edge marks every safe square, and every other `O` is captured. Each square is marked once, so the work is in proportion to the board's squares. The search keeps the squares to visit on a list, not in calls: one of the tests' boards has a region that winds {% $fig.longest %} squares from the edge, too deep for a search that calls itself.
