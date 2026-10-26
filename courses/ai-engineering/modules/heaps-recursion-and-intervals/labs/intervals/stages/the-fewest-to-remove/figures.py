# The tests' longest list, as tests/test_remove.py sets it.
MEETINGS = 200_000


def figures():
    few = 40
    return {"meetings": f"{MEETINGS:,}", "few": f"{few}", "subsets": f"{2**few:,}"}
