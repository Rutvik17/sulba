# The deepest row the tests ask about, as tests/test_symbols.py sets it.
ROWS = 60


def figures():
    return {"rows": f"{ROWS}", "length": f"{2 ** (ROWS - 1):,}"}
