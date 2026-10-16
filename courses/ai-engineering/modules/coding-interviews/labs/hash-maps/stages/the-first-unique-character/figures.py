# The longest test, as tests/test_unique.py sets it: its characters, and the characters that
# counting each one afresh reads.
CHARACTERS = 300_000


def figures():
    return {"characters": f"{CHARACTERS:,}", "reads": f"{CHARACTERS * CHARACTERS:,}"}
