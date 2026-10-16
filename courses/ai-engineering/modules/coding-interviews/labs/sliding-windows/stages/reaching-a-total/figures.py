# The longest test, as tests/test_reach.py sets it: its numbers, and the runs they make.
NUMBERS = 100_000


def figures():
    return {"numbers": f"{NUMBERS:,}", "runs": f"{NUMBERS * (NUMBERS + 1) // 2:,}"}
