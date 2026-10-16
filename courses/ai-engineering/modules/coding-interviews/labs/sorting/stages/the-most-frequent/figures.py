# The longest test, as tests/test_frequent.py sets it: its items and how many different ones, and
# the reads that counting each different item over the whole list makes.
ITEMS = 200_000
KINDS = 20_000


def figures():
    return {"items": f"{ITEMS:,}", "kinds": f"{KINDS:,}", "reads": f"{ITEMS * KINDS:,}"}
