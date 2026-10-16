# The longest test, as tests/test_anagram_starts.py sets it: its text and word, and how many runs
# of the word's length the text holds.
CHARACTERS = 100_000
LENGTH = 4_000


def figures():
    runs = CHARACTERS - LENGTH + 1
    return {
        "characters": f"{CHARACTERS:,}",
        "length": f"{LENGTH:,}",
        "runs": f"{runs:,}",
    }
