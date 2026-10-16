# The longest test, as tests/test_windows.py sets it: its numbers and its window, and the additions
# that summing each window afresh takes.
NUMBERS = 100_000
WIDTH = 50_000


def figures():
    additions = (NUMBERS - WIDTH + 1) * WIDTH
    return {
        "numbers": f"{NUMBERS:,}",
        "width": f"{WIDTH:,}",
        "additions": f"{additions:,}",
    }
