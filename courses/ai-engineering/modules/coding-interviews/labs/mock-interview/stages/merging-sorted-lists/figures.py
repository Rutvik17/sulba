# The longest case, as tests/test_merge.py sets it: its lists and their length, and the looks that
# checking every list's next number, for each number merged, makes.
LISTS = 4_000
LENGTH = 50


def figures():
    looks = LISTS * LENGTH * LISTS
    return {"lists": f"{LISTS:,}", "length": f"{LENGTH:,}", "looks": f"{looks:,}"}
