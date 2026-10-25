# The tests' longest text, as tests/test_parts.py sets it.
LETTERS = 200_000


def figures():
    return {"letters": f"{LETTERS:,}", "cuts": f"{LETTERS - 1:,}"}
