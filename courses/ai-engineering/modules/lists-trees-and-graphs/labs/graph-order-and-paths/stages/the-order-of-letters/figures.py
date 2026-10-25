# The longest test, as tests/test_letters.py sets it, and the pairs that comparing every word with
# every other makes.
WORDS = 50_000


def figures():
    return {"words": f"{WORDS:,}", "pairs": f"{WORDS * (WORDS - 1) // 2:,}"}
