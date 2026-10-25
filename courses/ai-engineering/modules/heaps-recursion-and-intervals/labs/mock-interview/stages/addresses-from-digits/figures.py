from math import comb

# The tests' longest string, as tests/test_addresses.py sets it.
DIGITS = 10_000


def figures():
    return {"digits": f"{DIGITS:,}", "ways": f"{comb(DIGITS - 1, 3):,}"}
