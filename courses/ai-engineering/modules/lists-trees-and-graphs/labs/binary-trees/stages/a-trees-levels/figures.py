# The largest test, as tests/test_levels.py sets it: a complete tree of this many nodes. And the
# items that pop(0) shifts when its nodes go through a list used as a queue: before the node at
# place is popped, the queue holds the nodes from place to the last child added.
LEVELS = 18
NODES = 2**LEVELS - 1


def figures():
    shifts = sum(min(2 * place, NODES - 1) - place for place in range(NODES))
    return {"nodes": f"{NODES:,}", "levels": f"{LEVELS}", "shifts": f"{shifts:,}"}
