def pair_sum(numbers, target):
    """The positions (i, j), i < j, of two numbers that add up to target, or None."""
    seen = {}
    for j, number in enumerate(numbers):
        i = seen.get(target - number)
        if i is not None:
            return (i, j)
        seen.setdefault(number, j)
    return None
