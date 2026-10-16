# The longest test, as tests/test_brackets.py sets it: DEPTH brackets opened and then closed, and
# what removing touching pairs pass by pass reads, one pair a pass, the text two shorter each time.
CHARACTERS = 200_000
DEPTH = CHARACTERS // 2


def figures():
    read = sum(CHARACTERS - 2 * done for done in range(DEPTH))
    return {
        "characters": f"{CHARACTERS:,}",
        "depth": f"{DEPTH:,}",
        "passes": f"{DEPTH:,}",
        "read": f"{read:,}",
    }
