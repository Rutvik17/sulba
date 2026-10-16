# The longest test, as tests/test_rotated.py sets it: its numbers and searches, and what reading
# from the start of the list takes for each search at most.
NUMBERS = 200_000
SEARCHES = 50_000


def figures():
    return {
        "numbers": f"{NUMBERS:,}",
        "searches": f"{SEARCHES:,}",
        "reads": f"{NUMBERS * SEARCHES:,}",
    }
