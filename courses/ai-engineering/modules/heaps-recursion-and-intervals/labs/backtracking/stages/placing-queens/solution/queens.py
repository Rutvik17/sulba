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
