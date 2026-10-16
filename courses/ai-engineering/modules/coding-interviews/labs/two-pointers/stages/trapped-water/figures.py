# The longest test, as tests/test_rain.py sets it: its bars, and the reads that scanning the whole
# row for every bar makes.
BARS = 100_000


def figures():
    return {"bars": f"{BARS:,}", "reads": f"{BARS * BARS:,}"}
