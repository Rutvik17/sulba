from itertools import accumulate


def range_sums(numbers, ranges):
    """The sum of numbers[start:stop] for each (start, stop) in ranges."""
    totals = [0, *accumulate(numbers)]
    return [totals[stop] - totals[start] for start, stop in ranges]
