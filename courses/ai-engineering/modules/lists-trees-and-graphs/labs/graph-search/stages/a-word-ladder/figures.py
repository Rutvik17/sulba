# The longest test, as tests/test_ladder.py sets it: random words of this many letters, with one
# ladder through them, and the pairs of words that comparing each with every other makes.
OTHERS = 5_000
LETTERS = 6


def figures():
    words = OTHERS + LETTERS
    return {
        "words": f"{words:,}",
        "letters": f"{LETTERS}",
        "pairs": f"{words * (words - 1) // 2:,}",
    }
