# The longest test, as tests/test_patterns.py sets it: texts of this many different characters,
# and the characters that finding where each first appears, in both texts, searches.
CHARACTERS = 200_000


def figures():
    searched = 2 * CHARACTERS * (CHARACTERS + 1) // 2
    return {"characters": f"{CHARACTERS:,}", "searched": f"{searched:,}"}
