from itertools import product
from math import comb

# The most pairs the tests ask for, as tests/test_brackets.py sets it.
PAIRS = 12


def balanced(text):
    depth = 0
    for bracket in text:
        depth += 1 if bracket == "(" else -1
        if depth < 0:
            return False
    return depth == 0


def figures():
    # The Catalan numbers, checked against counting every string, up to 8 pairs.
    for pairs in range(9):
        every = sum(balanced(text) for text in product("()", repeat=2 * pairs))
        assert every == comb(2 * pairs, pairs) // (pairs + 1)
    return {
        "pairs": f"{PAIRS}",
        "count": f"{comb(2 * PAIRS, PAIRS) // (PAIRS + 1):,}",
        "length": f"{2 * PAIRS}",
        "strings": f"{2 ** (2 * PAIRS):,}",
    }
