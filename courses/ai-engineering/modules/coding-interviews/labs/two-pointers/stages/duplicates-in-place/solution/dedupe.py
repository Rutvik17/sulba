def dedupe(numbers):
    """Move each different value of the sorted numbers to its front; return how many."""
    kept = 0
    for number in numbers:
        if kept == 0 or number != numbers[kept - 1]:
            numbers[kept] = number
            kept += 1
    return kept
