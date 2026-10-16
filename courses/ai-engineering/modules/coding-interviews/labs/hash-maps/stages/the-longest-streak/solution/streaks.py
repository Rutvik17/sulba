def longest_streak(numbers):
    """The length of the longest streak of consecutive integers among numbers."""
    present = set(numbers)
    best = 0
    for number in present:
        if number - 1 not in present:
            end = number
            while end + 1 in present:
                end += 1
            best = max(best, end - number + 1)
    return best
