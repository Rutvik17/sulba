# The longest test, as tests/test_sorted_pair.py sets it: its numbers, and the pairs they make.
NUMBERS = 200_000


def figures():
    return {"numbers": f"{NUMBERS:,}", "pairs": f"{NUMBERS * (NUMBERS - 1) // 2:,}"}
