# The day the limit check runs, as checks/test_day.py sets it: its codes, its limit, and the
# seconds its lookups take, the first code's slow.
import heapq

CODES = 100
LIMIT = 8
SLOW = 2
LATENCY = 0.25


def finished(seconds, limit):
    """When lookups taking these seconds have all ended, limit at a time, each started as
    soon as a slot frees."""
    slots = [0.0] * limit
    for each in seconds:
        heapq.heappush(slots, heapq.heappop(slots) + each)
    return max(slots)


def figures():
    day = finished([SLOW] + [LATENCY] * (CODES - 1), LIMIT)
    return {
        "codes": f"{CODES}",
        "limit": f"{LIMIT}",
        "slow": f"{SLOW}",
        "latency": f"{LATENCY}",
        "day": f"{day:g}",
    }
