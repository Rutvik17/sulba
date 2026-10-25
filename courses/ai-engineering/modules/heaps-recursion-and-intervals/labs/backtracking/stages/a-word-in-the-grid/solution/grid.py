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
