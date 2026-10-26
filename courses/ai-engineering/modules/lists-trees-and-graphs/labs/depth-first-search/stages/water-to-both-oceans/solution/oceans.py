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
