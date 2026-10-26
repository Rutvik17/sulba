from math import comb

# The tests' longest lists, as tests/test_totals.py sets them.
NUMBERS = 40
ONES = 40


def figures():
    return {
        "numbers": f"{NUMBERS}",
        "subsets": f"{2**NUMBERS:,}",
        "ones": f"{ONES}",
        "half": f"{ONES // 2}",
        "ways": f"{comb(ONES, ONES // 2):,}",
    }
