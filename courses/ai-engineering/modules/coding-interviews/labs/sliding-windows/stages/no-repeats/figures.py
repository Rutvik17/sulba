# The longest test, as tests/test_no_repeats.py sets it: a text cycling through KINDS different
# characters, and the characters that growing a run from every start until a repeat reads.
CHARACTERS = 100_000
KINDS = 20_000


def figures():
    # From each start the run grows over KINDS characters and reads one more, the repeat, unless
    # the text ends first.
    reads = sum(min(KINDS + 1, CHARACTERS - start) for start in range(CHARACTERS))
    return {
        "characters": f"{CHARACTERS:,}",
        "kinds": f"{KINDS:,}",
        "reads": f"{reads:,}",
    }
