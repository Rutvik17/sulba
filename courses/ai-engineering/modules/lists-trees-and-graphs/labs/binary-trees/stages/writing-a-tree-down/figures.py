# The largest test, as tests/test_codec.py sets it, its tokens, a value or a mark for each
# node and each missing child, and the shifts that taking each with pop(0) makes.
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
    tokens = 2 * len(found) + 1
    return {
        "nodes": f"{len(found):,}",
        "levels": f"{max(found) + 1}",
        "tokens": f"{tokens:,}",
        "shifts": f"{tokens * (tokens - 1) // 2:,}",
    }
