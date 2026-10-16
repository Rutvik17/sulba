def shortest_reach(numbers, target):
    """The length of the shortest run whose sum is at least target, or 0."""
    best = 0
    total = start = 0
    for end, number in enumerate(numbers):
        total += number
        while total >= target:
            if best == 0 or end - start + 1 < best:
                best = end - start + 1
            total -= numbers[start]
            start += 1
    return best
