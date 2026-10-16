# The longest test, as tests/test_dedupe.py sets it: this many numbers, each value twice, and the
# moves that deleting each value's second copy makes, shifting back every item after it.
NUMBERS = 1_000_000


def figures():
    values = NUMBERS // 2
    # Value v's second copy sits at v + 1 once the earlier repeats are gone, in a list of
    # NUMBERS - v items, so NUMBERS - 2v - 2 items come after it.
    moves = sum(NUMBERS - 2 * value - 2 for value in range(values))
    return {"numbers": f"{NUMBERS:,}", "moves": f"{moves:,}"}
