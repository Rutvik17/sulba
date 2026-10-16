# The longest test, as tests/test_first_last.py sets it: runs of RUN equal numbers, and what walking
# a whole run for each search reads at most.
NUMBERS = 200_000
RUN = 50_000
SEARCHES = 50_000


def figures():
    return {
        "numbers": f"{NUMBERS:,}",
        "run": f"{RUN:,}",
        "searches": f"{SEARCHES:,}",
        "reads": f"{RUN * SEARCHES:,}",
    }
