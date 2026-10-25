# The longest test, as tests/test_closest.py sets it.
POINTS = 50_000


def figures():
    return {"points": f"{POINTS:,}", "pairs": f"{POINTS * (POINTS - 1) // 2:,}"}
