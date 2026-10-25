```python
def both_oceans(heights):
    rows, columns = len(heights), len(heights[0]) if heights else 0

    def reached(starts):
        seen = set(starts)
        stack = list(starts)
        while stack:
            r, c = stack.pop()
            for nr, nc in ((r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)):
                if (
                    0 <= nr < rows
                    and 0 <= nc < columns
                    and (nr, nc) not in seen
                    and heights[nr][nc] >= heights[r][c]
                ):
                    seen.add((nr, nc))
                    stack.append((nr, nc))
        return seen

    pacific = reached([(0, c) for c in range(columns)] + [(r, 0) for r in range(rows)])
    atlantic = reached(
        [(rows - 1, c) for c in range(columns)]
        + [(r, columns - 1) for r in range(rows)]
    )
    return sorted(pacific & atlantic)
```

Rain flowing downhill from a square to an ocean is, read backwards, a climb from that ocean's edge to the square through neighbours at least as high. So one search from all the Pacific's edge squares, climbing, finds every square that drains into the Pacific, another finds the Atlantic's, and the answer is the squares in both. Each search visits a square at most once, so the work is in proportion to the squares, where a search from every square repeats the work for each of the {% $fig.squares %} squares of the tests' largest grid.
