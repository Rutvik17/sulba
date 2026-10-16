# The longest test, as tests/test_triples.py sets it: its numbers, and the triples of positions
# they make.
NUMBERS = 1_500


def figures():
    triples = NUMBERS * (NUMBERS - 1) * (NUMBERS - 2) // 6
    return {"numbers": f"{NUMBERS:,}", "triples": f"{triples:,}"}
