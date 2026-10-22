# The longest test, as tests/test_lru.py sets it, and the most steps that list.remove takes
# over its operations: each one can search the whole cache.
OPERATIONS = 200_000
CAPACITY = 50_000


def figures():
    return {
        "operations": f"{OPERATIONS:,}",
        "capacity": f"{CAPACITY:,}",
        "searches": f"{OPERATIONS * CAPACITY:,}",
    }
