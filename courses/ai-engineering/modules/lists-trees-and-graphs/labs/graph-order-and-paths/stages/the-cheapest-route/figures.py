# The largest test, as tests/test_route.py sets it: a long cheap way with too many stops, a dearer
# way with few enough, and flights that never beat either.
CITIES = 1_000
EXTRA = 20_000
STOPS = 30


def figures():
    return {
        "cities": f"{CITIES:,}",
        "flights": f"{(CITIES - 1) + 2 + EXTRA:,}",
        "stops": f"{STOPS}",
    }
