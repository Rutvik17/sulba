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
