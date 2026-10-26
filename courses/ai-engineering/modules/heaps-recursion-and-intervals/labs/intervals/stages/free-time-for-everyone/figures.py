# The tests' longest set of schedules, as tests/test_free.py sets it.
PEOPLE = 1_000
EACH = 200
SPAN = 10**9


def figures():
    return {"people": f"{PEOPLE:,}", "each": f"{EACH}", "span": f"{SPAN:,}"}
