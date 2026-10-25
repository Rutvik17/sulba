```python
def queens(size):
    columns, rising, falling = set(), set(), set()

    def place(row):
        if row == size:
            return 1
        ways = 0
        for column in range(size):
            if column in columns or row + column in rising or row - column in falling:
                continue
            columns.add(column)
            rising.add(row + column)
            falling.add(row - column)
            ways += place(row + 1)
            columns.remove(column)
            rising.remove(row + column)
            falling.remove(row - column)
        return ways

    return place(0)
```

Each row holds one queen, so the search places them row by row and only has to check columns and diagonals. The squares of a rising diagonal share `row + column`, and those of a falling diagonal share `row - column`, so three sets tell in one step whether a square is attacked. A queen is placed, the ways for the rows below are counted, and the queen is taken back before the next column is tried: {% $fig.ways %} ways for the tests' {% $fig.size %} queens.

Trying every order of the columns, one queen to a row, and checking the diagonals of each is the slow way: {% $fig.orders %} orders for {% $fig.size %} queens.
