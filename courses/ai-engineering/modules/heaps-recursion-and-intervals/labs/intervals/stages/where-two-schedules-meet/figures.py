# The tests' longest lists, as tests/test_meet.py sets them.
INTERVALS = 100_000


def figures():
    return {"intervals": f"{INTERVALS:,}", "pairs": f"{INTERVALS * INTERVALS:,}"}
