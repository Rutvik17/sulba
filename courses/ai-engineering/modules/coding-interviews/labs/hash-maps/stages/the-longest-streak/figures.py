# The longest test, as tests/test_streaks.py sets it: one streak of this many numbers, and the
# steps that counting up from every one of them takes.
NUMBERS = 100_000


def figures():
    return {"numbers": f"{NUMBERS:,}", "steps": f"{NUMBERS * (NUMBERS + 1) // 2:,}"}
