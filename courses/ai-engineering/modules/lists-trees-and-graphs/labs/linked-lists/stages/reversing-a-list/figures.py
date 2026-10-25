import sys

# The longest test, as tests/test_reverse.py sets it.
NODES = 200_000


def figures():
    return {"nodes": f"{NODES:,}", "limit": f"{sys.getrecursionlimit():,}"}
