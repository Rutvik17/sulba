# The largest test, as tests/test_path_sum.py sets it, and the visits that working out the
# best ways down from each node's children separately makes: each node once for each node
# above it.
ARM = 400
BUSH = 511
BUSH_LEVELS = BUSH.bit_length()


def tall_depths():
    """The depth of every node of the tests' tall tree, as tests' tall() builds it."""
    found = [0]
    for _side in range(2):
        found += range(1, ARM + 1)
        for depth in range(1, ARM - 9):
            for level in range(BUSH_LEVELS):
                found += [depth + 1 + level] * 2**level
    return found


def figures():
    found = tall_depths()
    return {
        "nodes": f"{len(found):,}",
        "levels": f"{max(found) + 1}",
        "visits": f"{sum(found):,}",
    }
