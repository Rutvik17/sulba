def longest_climb(heights):
    rows, columns = len(heights), len(heights[0]) if heights else 0
    longest = {}
    cells = sorted(
        ((heights[r][c], r, c) for r in range(rows) for c in range(columns)),
        reverse=True,
    )
    for height, r, c in cells:
        best = 0
        for nr, nc in ((r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)):
            if 0 <= nr < rows and 0 <= nc < columns and heights[nr][nc] > height:
                best = max(best, longest[nr, nc])
        longest[r, c] = best + 1
    return max(longest.values(), default=0)
