# The tests' longest lists, as tests/test_queries.py sets them.
INTERVALS = 100_000
QUERIES = 100_000


def figures():
    return {
        "intervals": f"{INTERVALS:,}",
        "queries": f"{QUERIES:,}",
        "pairs": f"{INTERVALS * QUERIES:,}",
    }
