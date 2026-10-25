import sys

# The largest test, as tests/test_copy_graph.py sets it: one cycle of this many nodes.
NODES = 100_000


def figures():
    # The explanation says a copy that calls itself on each neighbour goes past the limit.
    assert sys.getrecursionlimit() < NODES
    return {"nodes": f"{NODES:,}"}
