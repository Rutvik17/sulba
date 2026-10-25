```python
from collections import Counter


def traced(grid, word):
    rows, columns = len(grid), len(grid[0]) if grid else 0
    if Counter(word) - Counter("".join(grid)):
        return False
    used = set()

    def follow(row, column, place):
        if grid[row][column] != word[place] or (row, column) in used:
            return False
        if place == len(word) - 1:
            return True
        used.add((row, column))
        for down, across in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            r, c = row + down, column + across
            if 0 <= r < rows and 0 <= c < columns and follow(r, c, place + 1):
                return True
        used.remove((row, column))
        return False

    return any(
        follow(row, column, 0) for row in range(rows) for column in range(columns)
    )
```

`Counter(word) - Counter("".join(grid))` keeps the letters the word needs more of than the grid has, and if there are any, no path can spell it. Then the search starts from each cell and follows the word a letter at a time into the four neighbours, with the cells of the path so far in `used`, so none is used twice. A dead end takes its cell back out, and a path that reaches the word's last letter ends the search.

Without the count, the tests' grid of one letter and a word of {% $fig.prefix %} of it and one letter the grid lacks sends the search down every path of {% $fig.prefix %} cells: up to {% $fig.paths %} paths from each of its {% $fig.cells %} cells.
