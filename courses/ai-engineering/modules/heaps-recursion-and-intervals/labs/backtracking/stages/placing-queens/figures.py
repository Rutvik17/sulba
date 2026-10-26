from math import factorial

# The tests' largest board, as tests/test_queens.py sets it.
SIZE = 11


def ways(size):
    """The placements, counted with a bit for each column and diagonal."""
    full = (1 << size) - 1

    def count(columns, rising, falling):
        if columns == full:
            return 1
        total, free = 0, full & ~(columns | rising | falling)
        while free:
            bit = free & -free
            free -= bit
            total += count(
                columns | bit, (rising | bit) << 1 & full, (falling | bit) >> 1
            )
        return total

    return count(0, 0, 0)


def figures():
    return {
        "size": f"{SIZE}",
        "ways": f"{ways(SIZE):,}",
        "orders": f"{factorial(SIZE):,}",
    }
