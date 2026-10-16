# The longest test, as tests/test_warmer.py sets it: days that cool, then a warmer last day, and
# the days that searching ahead from each one reads.
DAYS = 100_000


def figures():
    reads = sum(DAYS - 1 - day for day in range(DAYS))
    return {"days": f"{DAYS:,}", "reads": f"{reads:,}"}
