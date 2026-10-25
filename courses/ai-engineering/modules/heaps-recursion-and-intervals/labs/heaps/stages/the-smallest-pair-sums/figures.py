# The longest test, as tests/test_pairs.py sets it.
SIZE = 100_000
K = 1_000


def figures():
    return {"size": f"{SIZE:,}", "k": f"{K:,}", "pairs": f"{SIZE * SIZE:,}"}
