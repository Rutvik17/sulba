# The longest test, as tests/test_medians.py sets it.
NUMBERS = 200_000


def figures():
    return {"numbers": f"{NUMBERS:,}", "sorted": f"{NUMBERS * (NUMBERS + 1) // 2:,}"}
