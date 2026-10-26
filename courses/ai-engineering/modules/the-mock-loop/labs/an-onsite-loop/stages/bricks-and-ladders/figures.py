# The tests' longest row, as tests/test_climb.py sets it.
BUILDINGS = 100_000


def figures():
    steps = BUILDINGS - 1
    return {"buildings": f"{BUILDINGS:,}", "sorted": f"{steps * (steps + 1) // 2:,}"}
