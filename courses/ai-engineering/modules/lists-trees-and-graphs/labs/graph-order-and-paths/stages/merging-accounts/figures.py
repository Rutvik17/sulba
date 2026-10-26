# The longest test, as tests/test_accounts.py sets it: accounts that each share an address with
# the next, and the pairs that a first pass comparing every account with every other makes.
ACCOUNTS = 50_000


def figures():
    return {
        "accounts": f"{ACCOUNTS:,}",
        "pairs": f"{ACCOUNTS * (ACCOUNTS - 1) // 2:,}",
    }
