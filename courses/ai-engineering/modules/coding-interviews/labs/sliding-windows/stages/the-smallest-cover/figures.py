# The longest test, as tests/test_cover.py sets it: a text whose only x and y sit at X and Y, and
# the characters that growing a run from every start until it covers "xy" reads.
CHARACTERS = 100_000
X = 30_000
Y = 70_000


def figures():
    # A run from a start up to X covers "xy" once it reaches Y; a later start never covers it,
    # and reads to the end of the text.
    reads = sum(Y - start + 1 for start in range(X + 1))
    reads += sum(CHARACTERS - start for start in range(X + 1, CHARACTERS))
    return {"characters": f"{CHARACTERS:,}", "reads": f"{reads:,}"}
