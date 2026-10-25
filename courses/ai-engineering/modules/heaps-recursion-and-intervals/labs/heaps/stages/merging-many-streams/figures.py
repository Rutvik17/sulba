# The longest test, as tests/test_merging.py sets it.
STREAMS = 2_000
ITEMS = 200_000


def figures():
    return {
        "streams": f"{STREAMS:,}",
        "items": f"{ITEMS:,}",
        "looks": f"{STREAMS * ITEMS:,}",
    }
