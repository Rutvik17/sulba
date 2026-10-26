# The longest test, as tests/test_ropes.py sets it.
ROPES = 200_000


def figures():
    # Each join looks through the ropes left, from ROPES down to 2.
    looks = sum(range(2, ROPES + 1))
    return {"ropes": f"{ROPES:,}", "joins": f"{ROPES - 1:,}", "looks": f"{looks:,}"}
