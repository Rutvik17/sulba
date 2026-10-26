# The tests' largest grid, as tests/test_climb.py sets it.
SIDE = 300


def figures():
    squares = SIDE * SIDE
    # From the snake's kth square the climb goes on through every square after it.
    return {
        "side": f"{SIDE}",
        "squares": f"{squares:,}",
        "visits": f"{squares * (squares + 1) // 2:,}",
    }
