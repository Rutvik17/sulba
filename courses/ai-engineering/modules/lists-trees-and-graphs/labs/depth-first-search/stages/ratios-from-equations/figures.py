# The tests' longest lists, as tests/test_ratios.py sets them.
VARIABLES = 100_000
QUERIES = 100_000


def figures():
    return {
        "equations": f"{VARIABLES - 1:,}",
        "queries": f"{QUERIES:,}",
        "walks": f"{QUERIES * VARIABLES:,}",
    }
