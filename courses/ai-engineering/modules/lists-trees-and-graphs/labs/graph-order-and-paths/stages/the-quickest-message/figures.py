# The largest test, as tests/test_delay.py sets it: a chain of computers with links that never
# beat it, and the looks that finding each soonest computer by a pass over the computers makes.
COMPUTERS = 40_000
EXTRA = 80_000


def figures():
    return {
        "computers": f"{COMPUTERS:,}",
        "links": f"{COMPUTERS - 1 + EXTRA:,}",
        "looks": f"{COMPUTERS * COMPUTERS:,}",
    }
