# The longest test, as tests/test_ranges.py sets it: its numbers and its ranges.
NUMBERS = 100_000
RANGES = 100_000


def figures():
    return {
        "numbers": f"{NUMBERS:,}",
        "ranges": f"{RANGES:,}",
        "additions": f"{NUMBERS * RANGES:,}",
    }
