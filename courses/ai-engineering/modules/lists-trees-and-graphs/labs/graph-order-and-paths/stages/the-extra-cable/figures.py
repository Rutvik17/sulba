# The largest test, as tests/test_cables.py sets it: a chain of computers, each joined to the next,
# with the cable that closes the loop last. Searching from each cable's first end visits every
# computer the chain has joined to it so far.
COMPUTERS = 200_000


def figures():
    return {
        "computers": f"{COMPUTERS:,}",
        "visits": f"{COMPUTERS * (COMPUTERS + 1) // 2:,}",
    }
