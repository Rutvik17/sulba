# The largest test, as tests/test_groups.py sets it, and the splits of 40 people into two groups.
PEOPLE = 100_000


def figures():
    return {"people": f"{PEOPLE:,}", "splits": f"{2**40:,}"}
