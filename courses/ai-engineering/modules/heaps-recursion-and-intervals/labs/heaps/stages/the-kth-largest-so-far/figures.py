# The longest test, as tests/test_kth.py sets it.
K = 1_000
ADDS = 200_000


def figures():
    start = K - 1
    sorted_in_all = sum(start + n for n in range(1, ADDS + 1))
    return {"adds": f"{ADDS:,}", "k": f"{K:,}", "sorted": f"{sorted_in_all:,}"}
