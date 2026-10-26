# The tests' largest circle, as tests/test_circle.py sets it.
PEOPLE = 1_000_000


def figures():
    return {"people": f"{PEOPLE:,}", "leave": f"{PEOPLE - 1:,}"}
