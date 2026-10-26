import sys

# The largest test, as tests/test_order.py sets it: a chain of courses, each needing the one
# before it, given in reverse, and the looks that finding each ready course by a pass over the
# courses left makes.
COURSES = 100_000


def figures():
    # The explanation says a search that calls itself along the chain goes past the limit.
    assert sys.getrecursionlimit() < COURSES
    return {
        "courses": f"{COURSES:,}",
        "looks": f"{COURSES * (COURSES + 1) // 2:,}",
    }
