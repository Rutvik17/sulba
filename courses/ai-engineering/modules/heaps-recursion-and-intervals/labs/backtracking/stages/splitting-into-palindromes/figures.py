# The tests' longest texts, as tests/test_palindromes.py sets them.
REPEATED = 18
LETTERS = 40


def figures():
    return {
        "repeated": f"{REPEATED}",
        "splits": f"{2 ** (REPEATED - 1):,}",
        "letters": f"{LETTERS}",
        "cuts": f"{2 ** (LETTERS - 1):,}",
    }
