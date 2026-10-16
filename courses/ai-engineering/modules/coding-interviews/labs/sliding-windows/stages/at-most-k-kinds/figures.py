# The longest test, as tests/test_kinds.py sets it: STRETCH items cycling through K values, then
# items that are each new, and the items that growing a run from every start until it holds more
# than K values reads.
ITEMS = 100_000
STRETCH = 80_000
K = 5


def reads_from(start):
    """The items a run from start reads, up to and including the one that makes K + 1 values."""
    if start < STRETCH:
        # The rest of the stretch holds min(K, its length) values, and each item after it is a
        # new value, until there are K + 1.
        rest = STRETCH - start
        return rest + min(K + 1 - min(K, rest), ITEMS - STRETCH)
    return min(K + 1, ITEMS - start)


def figures():
    reads = sum(reads_from(start) for start in range(ITEMS))
    return {"items": f"{ITEMS:,}", "reads": f"{reads:,}"}
