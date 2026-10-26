# The longest test, as tests/test_inversions.py sets it.
NUMBERS = 100_000


def figures():
    return {"numbers": f"{NUMBERS:,}", "pairs": f"{NUMBERS * (NUMBERS - 1) // 2:,}"}
