```python
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
```

The longest climb from a square is 1 more than the longest from the best of its higher neighbours, and every square a climb steps to is higher. So taking the squares from highest to lowest, each square's higher neighbours are done when it's reached, and it takes one look at its four neighbours. That's a depth-first search with a memo, done in the order the search would finish the squares, and with the sort it takes time in proportion to n log n for n squares. The tests' grid rises along a snake, so its longest climb visits all {% $fig.squares %} squares.

A search from every square without a memo is the slow way: on the snake, the climbs from its {% $fig.squares %} squares visit at least {% $fig.visits %} squares between them.
