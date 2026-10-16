# The longest test, as tests/test_pairs.py sets it: its numbers, and the pairs they make.
NUMBERS = 100_000


def figures():
    return {"numbers": f"{NUMBERS:,}", "pairs": f"{NUMBERS * (NUMBERS - 1) // 2:,}"}
