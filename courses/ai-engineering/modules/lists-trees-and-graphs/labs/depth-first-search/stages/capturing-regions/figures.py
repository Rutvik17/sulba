# The tests' largest board, as tests/test_regions.py builds it.
SIDE = 300


def figures():
    # A region of Os that winds row by row, joined to the edge at one square.
    rows = [["X"] * SIDE for _ in range(SIDE)]
    for row in range(1, SIDE - 1, 2):
        for column in range(1, SIDE - 1):
            rows[row][column] = "O"
        if row + 1 < SIDE - 1:
            rows[row + 1][SIDE - 2 if row // 2 % 2 == 0 else 1] = "O"
    rows[1][0] = "O"
    return {"side": f"{SIDE}", "longest": f"{sum(row.count('O') for row in rows):,}"}
