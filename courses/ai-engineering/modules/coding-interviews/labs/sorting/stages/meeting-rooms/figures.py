# The longest test, as tests/test_rooms.py sets it: its meetings, and the checks that counting the
# meetings going on at each start, against every meeting, makes.
MEETINGS = 100_000


def figures():
    return {"meetings": f"{MEETINGS:,}", "checks": f"{MEETINGS * MEETINGS:,}"}
