```python
DIGITS = set("123456789")


def solved(grid):
    cells = [list(row) for row in grid]
    rows = [set(row) - {"."} for row in grid]
    columns = [{row[c] for row in grid} - {"."} for c in range(9)]
    boxes = [set() for _ in range(9)]
    for r in range(9):
        for c in range(9):
            if grid[r][c] != ".":
                boxes[r // 3 * 3 + c // 3].add(grid[r][c])
    empty = [(r, c) for r in range(9) for c in range(9) if grid[r][c] == "."]

    def groups(r, c):
        return rows[r], columns[c], boxes[r // 3 * 3 + c // 3]

    def options(r, c):
        row, column, box = groups(r, c)
        return sorted(DIGITS - row - column - box)

    def fill():
        if not empty:
            return True
        place = min(range(len(empty)), key=lambda each: len(options(*empty[each])))
        r, c = empty.pop(place)
        for digit in options(r, c):
            cells[r][c] = digit
            for group in groups(r, c):
                group.add(digit)
            if fill():
                return True
            for group in groups(r, c):
                group.remove(digit)
        cells[r][c] = "."
        empty.insert(place, (r, c))
        return False

    fill()
    return ["".join(row) for row in cells]
```

The search fills the empty cell with the fewest digits left first. A cell with one digit left is forced, and a cell with none ends the branch at once, so the search spends its guesses where there are fewest to make. Each row, column and box keeps a set of its digits, so a digit's fit takes three lookups. A digit is placed, the rest is filled, and the digit is taken back if that fails.

Filling the cells in order, top left to bottom right, is the slow way: a wrong digit is often found out only many cells later, and every cell between is filled again for each digit tried. On the tests' hardest puzzle, it places {% $fig.plain %} digits, against {% $fig.fewest_first %} for the fewest-left search.
