from collections import Counter


def count_runs(numbers, target):
    """How many runs of one or more adjacent numbers add up to target."""
    sums = Counter({0: 1})
    total = count = 0
    for number in numbers:
        total += number
        count += sums[total - target]
        sums[total] += 1
    return count
