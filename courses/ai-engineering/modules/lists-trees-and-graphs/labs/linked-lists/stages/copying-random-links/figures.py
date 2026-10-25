# The longest test, as tests/test_copy.py sets it, and the steps that walking from the head
# of the original, then of the copy, to each random node's place takes: twice its place.
NODES = 100_000


def figures():
    walks = sum(2 * (NODES // 2 + index % (NODES // 2)) for index in range(NODES))
    return {"nodes": f"{NODES:,}", "walks": f"{walks:,}"}
