# The longest test, as tests/test_palindromes.py sets it: its characters, and how many characters
# cutting one off each end at each step copies, a slice two shorter each time.
CHARACTERS = 200_000


def figures():
    copied = sum(range(CHARACTERS - 2, 0, -2))
    return {"characters": f"{CHARACTERS:,}", "copied": f"{copied:,}"}
