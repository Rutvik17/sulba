# The longest test, as tests/test_water.py sets it: its lines, and the pairs they make.
LINES = 100_000


def figures():
    return {"lines": f"{LINES:,}", "pairs": f"{LINES * (LINES - 1) // 2:,}"}
