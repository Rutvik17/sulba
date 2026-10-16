# The longest test, as tests/test_min_stack.py sets it: this many values pushed, with the minimum
# asked for after each, and the values that min over the whole stack reads each time.
VALUES = 100_000


def figures():
    reads = VALUES * (VALUES + 1) // 2
    return {"values": f"{VALUES:,}", "reads": f"{reads:,}"}
