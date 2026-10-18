# The batch the tests run gradcheck on, and the digits it's scored against.
ROWS, DIGITS = 6, 10


def figures():
    return {"rows": str(ROWS), "classes": str(DIGITS), "entries": str(ROWS * DIGITS)}
