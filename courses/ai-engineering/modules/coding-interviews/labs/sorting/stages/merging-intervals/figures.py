# The longest test, as tests/test_intervals.py sets it: its intervals, and the pairs they make.
INTERVALS = 100_000


def figures():
    pairs = INTERVALS * (INTERVALS - 1) // 2
    return {"intervals": f"{INTERVALS:,}", "pairs": f"{pairs:,}"}
