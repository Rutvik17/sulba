# The longest test, as tests/test_shipping.py sets it: its packages and days, and how many
# capacities trying each one from the heaviest package up tries before it ships in time.
import random

PACKAGES = 50_000
DAYS = 100


def days_needed(weights, capacity):
    needed, load = 1, 0
    for weight in weights:
        if load + weight > capacity:
            needed, load = needed + 1, 0
        load += weight
    return needed


def figures():
    rng = random.Random(54)
    weights = [rng.randint(1, 1000) for _ in range(PACKAGES)]
    low, high = max(weights), sum(weights)
    while low < high:
        middle = (low + high) // 2
        if days_needed(weights, middle) <= DAYS:
            high = middle
        else:
            low = middle + 1
    tried = low - max(weights) + 1
    return {"packages": f"{PACKAGES:,}", "days": f"{DAYS:,}", "tried": f"{tried:,}"}
