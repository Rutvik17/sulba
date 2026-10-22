# The longest test, as tests/test_reorder.py sets it, with the memory it allows the call, and
# the steps that walking from each front node to the last node of what's left takes: from the
# node at place taken to the one at place NODES - 1 - taken.
NODES = 200_000
ALLOWED = 64 * 1024


def figures():
    walks = sum(NODES - 1 - 2 * taken for taken in range(NODES // 2))
    return {
        "nodes": f"{NODES:,}",
        "walks": f"{walks:,}",
        "allowed": f"{ALLOWED // 1024} KiB",
    }
