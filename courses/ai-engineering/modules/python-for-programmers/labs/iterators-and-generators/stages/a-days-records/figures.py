# The day a check reports on, and the most it may hold at once, as checks/test_report.py
# sets them.
LINES = 10_000
MEMORY = 1_000_000


def figures():
    return {"lines": f"{LINES:,}", "memory": f"{MEMORY // 1_000_000} MB"}
