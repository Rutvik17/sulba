# The tests' longest run, as tests/test_bookings.py sets it.
BOOKINGS = 50_000


def figures():
    return {
        "bookings": f"{BOOKINGS:,}",
        "comparisons": f"{BOOKINGS * (BOOKINGS - 1) // 2:,}",
    }
