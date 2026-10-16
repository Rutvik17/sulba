def largest_run(numbers):
    """The largest sum of a run of one or more adjacent numbers."""
    best = ending = float("-inf")
    for number in numbers:
        ending = max(number, ending + number)
        best = max(best, ending)
    return best
