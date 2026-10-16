# The longest test, as tests/test_anagrams.py sets it: its words, and the pairs they make.
WORDS = 50_000


def figures():
    return {"words": f"{WORDS:,}", "pairs": f"{WORDS * (WORDS - 1) // 2:,}"}
